# app.py
# Este es el servidor principal del dashboard
# Maneja todas las rutas web y la comunicación en tiempo real

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import mqtt_client as mqtt_handler
import db
from config import Config

# Crear la aplicación Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = "invernadero_secreto_2026"
socketio = SocketIO(app, cors_allowed_origins="*")

# Darle acceso al socketio al módulo MQTT
# (para que pueda enviar datos al navegador cuando lleguen mensajes)
mqtt_handler.socketio_ref = socketio


# RUTAS PRINCIPALES
@app.route("/")
def index():
    """Página principal del dashboard"""
    return render_template("index.html")


# RUTAS DE DATOS (el JS las llama para obtener info)
@app.route("/api/estado")
def get_estado():
    """Devuelve el estado actual del invernadero"""
    return jsonify(mqtt_handler.estado_actual)


@app.route("/api/lecturas")
def get_lecturas():
    """Devuelve las últimas lecturas para las gráficas"""
    lecturas = db.obtener_ultimas_lecturas(50)
    # Convertir fechas a texto para poder enviarlas como JSON
    for l in lecturas:
        if "timestamp" in l:
            l["timestamp"] = l["timestamp"].strftime("%H:%M:%S")
    return jsonify(lecturas)


@app.route("/api/eventos")
def get_eventos():
    """Devuelve los últimos eventos del sistema"""
    eventos = db.obtener_ultimos_eventos(20)
    for e in eventos:
        if "timestamp" in e:
            e["timestamp"] = e["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(eventos)


@app.route("/api/comandos")
def get_comandos():
    """Devuelve los últimos comandos enviados"""
    comandos = db.obtener_ultimos_comandos(20)
    for c in comandos:
        if "timestamp" in c:
            c["timestamp"] = c["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(comandos)


@app.route("/api/arm64")
def get_arm64():
    """Devuelve los resultados de los módulos ARM64"""
    resultados = db.obtener_resultados_arm64()
    for r in resultados:
        if "timestamp" in r:
            r["timestamp"] = r["timestamp"].strftime("%d/%m %H:%M")
    return jsonify(resultados)


# RUTAS DE COMANDOS (botones del dashboard)
@app.route("/api/comando", methods=["POST"])
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
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)