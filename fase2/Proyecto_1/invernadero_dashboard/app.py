# app.py
# Este es el servidor principal del dashboard
# Maneja todas las rutas web y la comunicación en tiempo real

import hmac
import os
import secrets
from functools import wraps
from pathlib import Path

import requests                          # ← PUENTE HÍBRIDO: reenvío HTTP hacia la Raspberry Pi
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from flask_socketio import SocketIO
import mqtt_client as mqtt_handler
import db
from config import Config
from services.arm64_service import (
    execute_fase1_module,
    execute_fase2_module,
    execute_historical_analysis,
)


DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DASHBOARD_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent
HISTORICAL_COLUMNS = {
    "TEMP",
    "HUM_AIRE",
    "SOIL1",
    "SOIL2",
    "LUZ",
    "GAS",
}
FASE2_MODULES = {
    1: "modulo_rmse",
    2: "modulo_2_regresion",
    3: "modulo_3_prediccion",
    4: "modulo_4_integral_error",
    5: "modulo_5_derivada_local",
}
FASE2_MODULE_NAMES = {name: number for number, name in FASE2_MODULES.items()}

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE ENTORNO HÍBRIDO
# Cuando PORT está definido, el proceso corre en Render (nube x86_64).
# Cuando PORT no está definido, corre directamente en la Raspberry Pi (ARM64).
# RASPBERRY_URL apunta al servidor Flask local de la Pi para el puente HTTP.
# ---------------------------------------------------------------------------
RASPBERRY_URL = os.environ.get("RASPBERRY_URL")          # ej: "http://192.168.1.42:5000"
_EN_RENDER = bool(os.environ.get("PORT"))                # True únicamente en Render

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)
#CORS(app, origins=["https://vercel.app"])

dashboard_secret = os.getenv("DASHBOARD_SECRET_KEY", "").strip()
if not dashboard_secret:
    dashboard_secret = secrets.token_urlsafe(32)
    print(
        "[LOGIN] ADVERTENCIA: DASHBOARD_SECRET_KEY no está configurada. "
        "Las sesiones se invalidarán al reiniciar."
    )

app.config["SECRET_KEY"] = dashboard_secret

DASHBOARD_USER = os.getenv("DASHBOARD_USER", "").strip()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

socketio = SocketIO(app, cors_allowed_origins="*")

# Darle acceso al socketio al módulo MQTT
# (para que pueda enviar datos al navegador cuando lleguen mensajes)
mqtt_handler.socketio_ref = socketio


def login_required(view_function):
    """Redirige al login cuando no existe una sesión autenticada."""
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


def resolve_historical_file_path(file_path):
    """Resuelve una ruta histórica absoluta o relativa al proyecto."""
    path = Path(file_path).expanduser()

    if path.is_absolute():
        candidates = [path]
    else:
        candidates = [
            WORKSPACE_DIR / path,
            PROJECT_DIR / path,
        ]

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved

    return None


# ---------------------------------------------------------------------------
# HELPER DE PUENTE HÍBRIDO
# Reenvía la petición HTTP entrante hacia la Raspberry Pi y devuelve su
# respuesta exacta. Se reutiliza en las tres rutas ARM64.
# ---------------------------------------------------------------------------
def _reenviar_a_raspberry(ruta_relativa):
    """
    Reenvía la petición actual (headers + JSON body) hacia RASPBERRY_URL.

    Parámetros
    ----------
    ruta_relativa : str
        La misma sub-ruta que se está procesando, ej: "/api/arm64/fase1/run".

    Retorna
    -------
    flask.Response con el JSON exacto que respondió la Raspberry Pi,
    o un error 502/503 si el puente falla.
    """
    if not RASPBERRY_URL:
        return jsonify({
            "ok": False,
            "error": "RASPBERRY_URL_NOT_SET",
            "detail": (
                "Este servidor corre en Render pero RASPBERRY_URL no está "
                "configurada. Define la variable de entorno RASPBERRY_URL "
                "apuntando al servidor Flask de la Raspberry Pi."
            ),
        }), 503

    destino = RASPBERRY_URL.rstrip("/") + ruta_relativa

    # Reenviamos los mismos headers relevantes (Content-Type, etc.)
    headers_reenvio = {
        k: v for k, v in request.headers
        if k.lower() in ("content-type", "accept", "x-request-id")
    }

    try:
        respuesta_pi = requests.request(
            method=request.method,
            url=destino,
            headers=headers_reenvio,
            json=request.get_json(silent=True),
            params=request.args,
            timeout=60,                  # los módulos ASM pueden tardar
        )
        return (
            respuesta_pi.content,
            respuesta_pi.status_code,
            {"Content-Type": "application/json"},
        )
    except requests.exceptions.ConnectionError as exc:
        return jsonify({
            "ok": False,
            "error": "RASPBERRY_UNREACHABLE",
            "detail": f"No se pudo conectar a la Raspberry Pi ({destino}): {exc}",
        }), 502
    except requests.exceptions.Timeout:
        return jsonify({
            "ok": False,
            "error": "RASPBERRY_TIMEOUT",
            "detail": f"La Raspberry Pi no respondió en 60 s ({destino})",
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "BRIDGE_ERROR",
            "detail": str(exc),
        }), 502


# RUTAS PRINCIPALES
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicia una sesión usando credenciales configuradas en .env."""
    if session.get("authenticated"):
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not DASHBOARD_USER or not DASHBOARD_PASSWORD:
            error = "Las credenciales del dashboard no están configuradas."
            return render_template("login.html", error=error), 503

        valid_user = hmac.compare_digest(username, DASHBOARD_USER)
        valid_password = hmac.compare_digest(password, DASHBOARD_PASSWORD)

        if valid_user and valid_password:
            session.clear()
            session["authenticated"] = True
            session["username"] = DASHBOARD_USER
            return redirect(url_for("index"))

        error = "Usuario o contraseña incorrectos."
        return render_template("login.html", error=error), 401

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Cierra la sesión actual."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    """Página principal del dashboard"""
    return render_template("index.html")


# RUTAS DE DATOS (el JS las llama para obtener info)
@app.route("/api/estado")
@login_required
def get_estado():
    """Devuelve el estado actual del invernadero"""
    return jsonify(mqtt_handler.estado_actual)


@app.route("/api/lecturas")
@login_required
def get_lecturas():
    """Devuelve las ultimas lecturas normalizadas para las graficas"""
    lecturas = db.obtener_ultimas_lecturas(50)
    return jsonify([normalizar_lectura_dashboard(l) for l in lecturas])


@app.route("/api/decision-arm64/latest")
@login_required
def get_decision_arm64_latest():
    """Devuelve la última decisión ARM64 válida."""
    lectura = db.obtener_ultima_decision_arm64()

    if not lectura:
        return jsonify({
            "ok": False,
            "message": "sin datos",
        })

    timestamp = lectura.get("timestamp") or lectura.get("fecha")
    decision = lectura.get("decision_arm64") or {}

    return jsonify({
        "ok": True,
        "decision_arm64": decision,
        "accion_ejecutada": lectura.get("accion_ejecutada"),
        "resultado_actuador": lectura.get("resultado_actuador"),
        "gpio_aplicado": lectura.get("gpio_aplicado"),
        "status_arm64": (
            lectura.get("status_arm64")
            or decision.get("status")
            or decision.get("STATUS")
        ),
        "timestamp": formatear_fecha_dashboard(timestamp),
    })


@app.route("/api/eventos")
@login_required
def get_eventos():
    """Devuelve los últimos eventos del sistema"""
    eventos = db.obtener_ultimos_eventos(20)
    for e in eventos:
        if "timestamp" in e:
            e["timestamp"] = e["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(eventos)


@app.route("/api/comandos")
@login_required
def get_comandos():
    """Devuelve los últimos comandos enviados"""
    comandos = db.obtener_ultimos_comandos(20)
    for c in comandos:
        if "timestamp" in c:
            c["timestamp"] = c["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(comandos)


@app.route("/api/arm64")
@login_required
def get_arm64():
    """Devuelve los resultados de los módulos ARM64"""
    resultados = db.obtener_resultados_arm64()
    for r in resultados:
        if "timestamp" in r:
            r["timestamp"] = r["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(resultados)


def formatear_fecha_dashboard(valor):
    """Convierte fecha o texto a una hora mostrable."""
    if hasattr(valor, "strftime"):
        return valor.strftime("%H:%M:%S")

    if valor is None:
        return "--"

    return str(valor)


def normalizar_lectura_dashboard(lectura):
    """Normaliza lecturas antiguas y lecturas completas de fase 2."""
    tipo = lectura.get("tipo")
    valor = lectura.get("valor")
    timestamp = lectura.get("timestamp") or lectura.get("fecha")

    normalizada = {
        "timestamp": formatear_fecha_dashboard(timestamp),
        "temperatura": lectura.get("temp"),
        "humedad_ambiente": lectura.get("hum"),
        "humedad_suelo_area1": lectura.get("val_s1"),
        "humedad_suelo_area2": lectura.get("val_s2"),
        "luz": lectura.get("val_luz"),
        "gas": lectura.get("val_gas"),
        "decision_arm64": lectura.get("decision_arm64") or {},
        "accion_ejecutada": lectura.get("accion_ejecutada"),
        "resultado_actuador": lectura.get("resultado_actuador"),
        "gpio_aplicado": lectura.get("gpio_aplicado"),
        "status_arm64": lectura.get("status_arm64"),
    }

    # esto mantiene compatibilidad con lecturas tipo valor
    if tipo in normalizada and normalizada[tipo] is None:
        normalizada[tipo] = valor

    return normalizada


def columna_modulo_valida(column):
    """Valida columna numerica o columna logica."""
    if isinstance(column, bool):
        return False

    if isinstance(column, str):
        stripped = column.strip().upper()
        if stripped.isdigit():
            return 2 <= int(stripped) <= 7
        return stripped in HISTORICAL_COLUMNS

    try:
        return 2 <= int(column) <= 7
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# 🚨 RUTA ARM64 — FASE 1
# Llama a execute_fase1_module que compila y ejecuta ensamblador ARM64.
# En Render: reenvía la petición íntegra a la Raspberry Pi física.
# En la Pi:  ejecuta el flujo nativo original sin cambios.
# ---------------------------------------------------------------------------
@app.route("/api/arm64/fase1/run", methods=["POST"])
@login_required
def run_arm64_fase1():
    """Ejecuta un módulo ARM64 de Fase 1 y guarda su resultado."""

    # ── FILTRO DE ENTORNO ──────────────────────────────────────────────────
    if _EN_RENDER:
        return _reenviar_a_raspberry("/api/arm64/fase1/run")
    # ── FIN FILTRO — a partir de aquí solo corre en la Raspberry Pi ────────

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_JSON",
            "detail": "Request body must be a JSON object",
        }), 400

    module_number = datos.get("module_number")
    column = datos.get("column", 2)
    file_path = datos.get("file_path") or "lecturas.csv"
    start_line_raw = datos.get("start_line", 1)
    end_line_raw = datos.get("end_line", 30)

    if isinstance(module_number, bool):
        module_number = None

    if isinstance(column, bool):
        column = None

    if isinstance(start_line_raw, bool) or isinstance(end_line_raw, bool):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    try:
        module_number = int(module_number)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_MODULE",
            "detail": "module_number must be an integer between 1 and 5",
        }), 400

    try:
        start_line = int(start_line_raw)
        end_line = int(end_line_raw)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    if module_number < 1 or module_number > 5:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_MODULE",
            "detail": "module_number must be between 1 and 5",
        }), 400

    if start_line < 1 or end_line < start_line:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "Invalid line range",
        }), 400

    if not isinstance(file_path, str) or not file_path.strip():
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_FILE_PATH",
            "detail": "file_path must be a non-empty string",
        }), 400

    if not columna_modulo_valida(column):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_COLUMN",
            "detail": "column must be 2..7 or TEMP, HUM_AIRE, SOIL1, SOIL2, LUZ, GAS",
        }), 400

    resultado = execute_fase1_module(
        module_number=module_number,
        column=column,
        file_path=file_path.strip(),
        start_line=start_line,
        end_line=end_line,
    )

    if not resultado.get("ok"):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": resultado.get("error", "EXECUTION_FAILED"),
            "detail": resultado.get(
                "detail",
                "The ARM64 module could not be executed",
            ),
        }), 500

    saved = db.guardar_resultado_arm64(resultado)

    if not saved:
        return jsonify({
            "ok": True,
            "saved": False,
            "warning": "DATABASE_SAVE_FAILED",
            "detail": "ARM64 completed, but MongoDB save failed",
            "data": resultado,
        }), 200

    return jsonify({
        "ok": True,
        "saved": True,
        "data": resultado,
    }), 200


# ---------------------------------------------------------------------------
# 🚨 RUTA ARM64 — FASE 2
# Llama a execute_fase2_module (módulos avanzados: RMSE, regresión, etc.)
# En Render: reenvía la petición íntegra a la Raspberry Pi física.
# En la Pi:  ejecuta el flujo nativo original sin cambios.
# ---------------------------------------------------------------------------
@app.route("/api/arm64/fase2/run", methods=["POST"])
@login_required
def run_arm64_fase2():
    """Ejecuta un módulo avanzado de Fase 2."""

    # ── FILTRO DE ENTORNO ──────────────────────────────────────────────────
    if _EN_RENDER:
        return _reenviar_a_raspberry("/api/arm64/fase2/run")
    # ── FIN FILTRO — a partir de aquí solo corre en la Raspberry Pi ────────

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "ok": False,
            "error": "INVALID_JSON",
            "detail": "Request body must be a JSON object",
        }), 400

    module_number_raw = datos.get("module_number")
    module_name_raw = datos.get("module_name")

    module_number = None
    if module_number_raw is not None and not isinstance(module_number_raw, bool):
        try:
            module_number = int(module_number_raw)
        except (TypeError, ValueError):
            module_number = None

    module_name = None
    if isinstance(module_name_raw, str):
        module_name = module_name_raw.strip()

    if module_number is None and module_name:
        module_number = FASE2_MODULE_NAMES.get(module_name)

    if module_number not in FASE2_MODULES:
        return jsonify({
            "ok": False,
            "error": "INVALID_MODULE",
            "detail": "module_number must be 1..5 or module_name must be allowed",
        }), 400

    file_path = datos.get("file_path") or "lecturas.csv"
    start_line_raw = datos.get("start_line", 1)
    end_line_raw = datos.get("end_line", 30)
    column_raw = datos.get("column", "TEMP")
    ideal = datos.get("ideal", 25)
    k = datos.get("k", 5)

    if not isinstance(file_path, str) or not file_path.strip():
        return jsonify({
            "ok": False,
            "error": "INVALID_FILE_PATH",
            "detail": "file_path must be a non-empty string",
        }), 400

    if isinstance(start_line_raw, bool) or isinstance(end_line_raw, bool):
        return jsonify({
            "ok": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    try:
        start_line = int(start_line_raw)
        end_line = int(end_line_raw)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    if start_line < 1 or end_line < start_line:
        return jsonify({
            "ok": False,
            "error": "INVALID_RANGE",
            "detail": "Invalid line range",
        }), 400

    if not isinstance(column_raw, str):
        return jsonify({
            "ok": False,
            "error": "INVALID_COLUMN",
            "detail": "column must be a string",
        }), 400

    column = column_raw.strip().upper()
    if column not in HISTORICAL_COLUMNS:
        return jsonify({
            "ok": False,
            "error": "INVALID_COLUMN",
            "detail": "column must be TEMP, HUM_AIRE, SOIL1, SOIL2, LUZ or GAS",
        }), 400

    resultado = execute_fase2_module(
        module_number=module_number,
        module_name=FASE2_MODULES[module_number],
        file_path=file_path.strip(),
        start_line=start_line,
        end_line=end_line,
        column=column,
        ideal=ideal,
        k=k,
    )

    status_code = 200 if resultado.get("ok") else 500
    return jsonify({
        "ok": bool(resultado.get("ok")),
        "error": resultado.get("error"),
        "detail": resultado.get("detail"),
        "parsed": resultado.get("parsed", {}),
        "raw_output": resultado.get("output_text", ""),
        "data": resultado,
    }), status_code


# ---------------------------------------------------------------------------
# 🚨 RUTA ARM64 — ANÁLISIS HISTÓRICO
# Llama a execute_historical_analysis y lee archivos CSV locales de la Pi.
# En Render: reenvía la petición íntegra a la Raspberry Pi física.
#            NOTA: resolve_historical_file_path NO se llama en Render porque
#            el archivo CSV existe físicamente solo en la Raspberry Pi.
# En la Pi:  ejecuta el flujo nativo original con resolución de ruta local.
# ---------------------------------------------------------------------------
@app.route("/api/arm64/historical/run", methods=["POST"])
@login_required
def run_arm64_historical():
    """Ejecuta el analizador histórico ARM64 y guarda su resultado."""

    # ── FILTRO DE ENTORNO ──────────────────────────────────────────────────
    if _EN_RENDER:
        return _reenviar_a_raspberry("/api/arm64/historical/run")
    # ── FIN FILTRO — a partir de aquí solo corre en la Raspberry Pi ────────

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_JSON",
            "detail": "Request body must be a JSON object",
        }), 400

    file_path = datos.get("file_path")
    start_line_raw = datos.get("start_line")
    end_line_raw = datos.get("end_line")
    column_raw = datos.get("column")

    if not isinstance(file_path, str) or not file_path.strip():
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_FILE_PATH",
            "detail": "file_path must be a non-empty string",
        }), 400

    resolved_path = resolve_historical_file_path(file_path.strip())
    if resolved_path is None:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "FILE_NOT_FOUND",
            "detail": f"Input file does not exist: {file_path}",
        }), 400

    if isinstance(start_line_raw, bool) or isinstance(end_line_raw, bool):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    try:
        start_line = int(start_line_raw)
        end_line = int(end_line_raw)
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
        }), 400

    if start_line < 1:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "start_line must be greater than or equal to 1",
        }), 400

    if end_line < start_line:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_RANGE",
            "detail": "end_line must be greater than or equal to start_line",
        }), 400

    if not isinstance(column_raw, str):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_COLUMN",
            "detail": "column must be a string",
        }), 400

    column = column_raw.strip().upper()
    if column not in HISTORICAL_COLUMNS:
        return jsonify({
            "ok": False,
            "saved": False,
            "error": "INVALID_COLUMN",
            "detail": f"Unsupported column: {column}",
        }), 400

    resultado = execute_historical_analysis(
        file_path=str(resolved_path),
        start_line=start_line,
        end_line=end_line,
        column=column,
    )

    if not resultado.get("ok"):
        return jsonify({
            "ok": False,
            "saved": False,
            "error": resultado.get("error", "EXECUTION_FAILED"),
            "detail": resultado.get(
                "detail",
                "Historical ARM64 analysis failed",
            ),
            "data": resultado,
        }), 500

    resultado["requested_file_path"] = file_path.strip()
    saved = db.guardar_resultado_historico_arm64(resultado)

    if not saved:
        return jsonify({
            "ok": True,
            "saved": False,
            "warning": "DATABASE_SAVE_FAILED",
            "detail": "ARM64 completed, but MongoDB save failed",
            "data": resultado,
        }), 200

    return jsonify({
        "ok": True,
        "saved": True,
        "data": resultado,
    }), 200


# RUTAS DE COMANDOS (botones del dashboard)
@app.route("/api/comando", methods=["POST"])
@login_required
def enviar_comando():
    """Recibe un comando del dashboard y lo publica por MQTT"""
    datos  = request.get_json()
    accion = datos.get("accion")
    valor  = datos.get("valor")

    if not accion or valor is None:
        return jsonify({"ok": False, "error": "Faltan datos"}), 400

    resultado = mqtt_handler.publicar_comando(accion, valor)

    if resultado:
        # Actualizar el estado local también
        if accion in ["riego", "riego_area1", "riego_area2"]:
            mqtt_handler.estado_actual["riego"] = "ON" if valor == "ON" else "OFF"
        elif accion == "ventilador":
            mqtt_handler.estado_actual["ventilador"] = valor
        elif accion == "luces":
            mqtt_handler.estado_actual["luces"] = valor
        elif accion == "alarma":
            mqtt_handler.estado_actual["alarma"] = valor

        # Notificar a todos los navegadores conectados
        socketio.emit("actualizacion", mqtt_handler.estado_actual)
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "Acción no reconocida"}), 400


@app.route("/api/modo", methods=["POST"])
@login_required
def cambiar_modo():
    """Cambia entre modo automático y manual"""
    datos = request.get_json()
    modo  = datos.get("modo", "AUTO")

    mqtt_handler.publicar_comando("control_remoto", f"MODO_{modo}")
    db.guardar_evento("MODO", f"Dashboard cambió a modo: {modo}")
    return jsonify({"ok": True, "modo": modo})


# EVENTOS SOCKETIO
@socketio.on("connect")
def on_connect():
    """Cuando un navegador se conecta, le mandamos el estado actual"""
    print("Navegador conectado al dashboard")
    socketio.emit("actualizacion", mqtt_handler.estado_actual)


@socketio.on("disconnect")
def on_disconnect():
    print("Navegador desconectado")


# INICIO DEL SERVIDOR
if __name__ == "__main__":
    print("Iniciando Dashboard Invernadero Inteligente...")
    print("─" * 45)

    # Iniciar conexión MQTT en segundo plano
    mqtt_handler.iniciar_mqtt()

    # Iniciar servidor web
    print("Servidor corriendo en: http://localhost:5000")
    print("─" * 45)
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )