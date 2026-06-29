import certifi
import ssl
from pymongo import MongoClient
from datetime import datetime, timezone
from config import Config

#client = MongoClient(Config.MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)



def _crear_cliente_mongo():
    try:
        return MongoClient(Config.MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    except Exception as exc:
        print(f"[MongoDB] No se pudo inicializar MongoClient: {exc}")
        return None


def _obtener_coleccion(nombre):
    if db is None:
        return None
    return db[nombre]


# Crear la conexión a la base de datos
client = _crear_cliente_mongo()
db     = client[Config.MONGO_DB] if client is not None else None

# --- Colecciones (como "tablas" en MongoDB) ---
sensor_readings = _obtener_coleccion("sensor_readings")   # lecturas de sensores
events          = _obtener_coleccion("events")            # alertas y eventos
commands        = _obtener_coleccion("commands")          # comandos enviados
system_status   = _obtener_coleccion("system_status")     # estado global actual
actuator_logs   = _obtener_coleccion("actuator_logs")     # historial de actuadores
arm64_results   = _obtener_coleccion("arm64_results")     # resultados de módulos ARM64

def guardar_resultado_arm64(resultado: dict) -> bool:
    """Guarda un resultado ARM64 sin propagar errores hacia Flask."""
    try:
        if not isinstance(resultado, dict):
            print("[MongoDB] Resultado ARM64 inválido: no es un diccionario.")
            return False

        collection = globals().get("arm64_results")
        if collection is None:
            collection = db["arm64_results"]
            globals()["arm64_results"] = collection

        documento = {
            "timestamp": datetime.now(timezone.utc),
            "source": "fase1_dashboard",
            "module": resultado.get("module"),
            "module_number": resultado.get("module_number"),
            "column": resultado.get("column"),
            "input": {
                "module_number": resultado.get("module_number"),
                "column": resultado.get("column"),
            },
            "result": resultado.get("parsed", {}),
            "raw_output": resultado.get("output_text", ""),
            "status": resultado.get("status", "ERROR"),
            "ok": bool(resultado.get("ok", False)),
            "error_detail": resultado.get("detail"),
        }

        collection.insert_one(documento)
        return True

    except Exception as exc:
        print(f"[MongoDB] Error guardando resultado ARM64: {exc}")
        return False


def guardar_resultado_historico_arm64(resultado: dict) -> bool:
    """Guarda un resultado histórico ARM64 sin propagar errores a Flask."""
    try:
        if not isinstance(resultado, dict):
            print("[MongoDB] Resultado histórico inválido: no es un diccionario.")
            return False

        collection = globals().get("arm64_results")
        if collection is None:
            collection = db["arm64_results"]
            globals()["arm64_results"] = collection

        file_path = resultado.get(
            "requested_file_path",
            resultado.get("file_path"),
        )
        start_line = resultado.get("start_line")
        end_line = resultado.get("end_line")
        column = resultado.get("column")

        documento = {
            "timestamp": datetime.now(timezone.utc),
            "source": "historical_analyzer",
            "module": "historical_analyzer",
            "input": {
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "column": column,
            },
            "range": {
                "start_line": start_line,
                "end_line": end_line,
            },
            "column": column,
            "result": resultado.get("parsed", {}),
            "raw_output": resultado.get("output_text", ""),
            "status": resultado.get("status", "ERROR"),
            "ok": bool(resultado.get("ok", False)),
            "error_detail": resultado.get("detail"),
        }

        collection.insert_one(documento)
        return True

    except Exception as exc:
        print(f"[MongoDB] Error guardando resultado histórico ARM64: {exc}")
        return False


def guardar_lectura(tipo, valor, origen="sensor"):
    """Guarda una lectura de sensor en MongoDB"""
    documento = {
        "timestamp": datetime.now(),
        "tipo":      tipo,
        "valor":     valor,
        "origen":    origen,
        "estado":    "activo"
    }
    sensor_readings.insert_one(documento)


def guardar_evento(tipo, descripcion, nivel="INFO"):
    """Guarda un evento o alerta en MongoDB"""
    documento = {
        "timestamp":   datetime.now(),
        "tipo":        tipo,
        "descripcion": descripcion,
        "nivel":       nivel,   # INFO, ADVERTENCIA, EMERGENCIA
        "origen":      "dashboard"
    }
    events.insert_one(documento)


def guardar_comando(accion, valor, origen="dashboard"):
    """Guarda cada comando enviado desde el dashboard"""
    documento = {
        "timestamp": datetime.now(),
        "accion":    accion,
        "valor":     valor,
        "origen":    origen
    }
    commands.insert_one(documento)


def actualizar_estado_global(estado):
    """Actualiza el estado global del invernadero"""
    system_status.replace_one(
        {},   # reemplaza el único documento de estado
        {
            "timestamp": datetime.now(),
            "estado":    estado
        },
        upsert=True   # si no existe, lo crea
    )


def obtener_ultimas_lecturas(limite=50):
    """Obtiene las últimas lecturas para las gráficas"""
    return list(
        sensor_readings
        .find({}, {"_id": 0})   # excluye el _id de MongoDB
        .sort("timestamp", -1)  # las más recientes primero
        .limit(limite)
    )


def obtener_ultima_decision_arm64():
    """Obtiene la lectura más reciente con una decisión ARM64 válida."""
    try:
        if sensor_readings is None:
            print("[MongoDB] No se pudo obtener decisión ARM64: base no disponible.")
            return None

        return sensor_readings.find_one(
            {
                "decision_arm64": {
                    "$exists": True,
                    "$ne": {},
                },
                "$or": [
                    {"status_arm64": {"$exists": True}},
                    {"decision_arm64.status": {"$exists": True}},
                ],
            },
            {"_id": 0},
            sort=[("timestamp", -1)],
        )

    except Exception as exc:
        print(f"[MongoDB] No se pudo obtener decisión ARM64: {exc}")
        return None


def obtener_ultimos_eventos(limite=20):
    """Obtiene los últimos eventos para el historial"""
    return list(
        events
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limite)
    )

def obtener_ultimos_comandos(limite=20):
    """Obtiene los últimos comandos enviados"""
    return list(
        commands
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limite)
    )


def obtener_resultados_arm64():
    """Obtiene los resultados de los módulos ARM64"""
    try:
        if arm64_results is None:
            print("[MongoDB] No se pudieron obtener resultados ARM64: base no disponible.")
            return []
        return list(
            arm64_results
            .find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(10)
        )
    except Exception as exc:
        print(f"[MongoDB] No se pudieron obtener resultados ARM64: {exc}")
        return []
