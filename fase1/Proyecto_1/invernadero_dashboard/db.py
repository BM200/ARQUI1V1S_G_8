# db.py
# Este archivo maneja toda la comunicación con MongoDB Atlas
# Aquí se guardan y leen los datos del invernadero

from pymongo import MongoClient
from datetime import datetime
from config import Config

# Crear la conexión a la base de datos
client = MongoClient(Config.MONGO_URI)
print("Conectando a Mongo...")
print(client.list_database_names())
db     = client[Config.MONGO_DB]

# --- Colecciones (como "tablas" en MongoDB) ---
sensor_readings = db["sensor_readings"]   # lecturas de sensores
events          = db["events"]            # alertas y eventos
commands        = db["commands"]          # comandos enviados
system_status   = db["system_status"]     # estado global actual
actuator_logs   = db["actuator_logs"]     # historial de actuadores
arm64_results   = db["arm64_results"]     # resultados de módulos ARM64


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
    return list(
        arm64_results
        .find({}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(10)
    )