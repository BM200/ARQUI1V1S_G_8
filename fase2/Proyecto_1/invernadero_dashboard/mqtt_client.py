# Este archivo maneja la conexión con el broker MQTT
# Escucha los datos que publica la Raspberry Pi
# y también puede enviar comandos hacia ella

import json
import paho.mqtt.client as mqtt
from datetime import datetime
from config import Config
import db

# Variable global para el socketio (se asigna desde app.py)
# Esto permite enviar datos al navegador en tiempo real
socketio_ref = None

# Estado actual del invernadero (se actualiza con cada mensaje MQTT)
estado_actual = {
    "temperatura":      "--",
    "humedad_ambiente": "--",
    "humedad_suelo_area1":  "--",
    "humedad_suelo_area2":  "--",
    "luz":              "--",
    "gas":              "--",
    "temperatura_estado": "",
    "humedad_ambiente_estado": "",
    "humedad_suelo_area1_estado": "",
    "humedad_suelo_area2_estado": "",
    "luz_estado": "",
    "gas_estado": "",
    "estado_global":    "DESCONECTADO",
    "riego":            "OFF",
    "ventilador":       "OFF",
    "luces":            "OFF",
    "alarma":           "OFF",
    "ultima_actualizacion": "--"
}


def on_connect(client, userdata, flags, rc):
    """Se ejecuta cuando el cliente se conecta al broker"""
    if rc == 0:
        print("Conectado al broker MQTT")
        # Suscribirse a todos los topics de sensores
        for topic in Config.TOPICS.values():
            client.subscribe(topic)
            print(f"   Suscrito a: {topic}")
    else:
        print(f"Error al conectar al broker MQTT. Código: {rc}")


# mqtt_client.py — reemplazar la función on_message completa

def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    topics  = Config.TOPICS

    print(f"MQTT recibido | {topic}: {payload}")

    try:
        # Todos nuestros sensores publican JSON
        datos = json.loads(payload)
    except json.JSONDecodeError:
        # Si llega texto plano, lo envolvemos
        datos = {"valor": payload, "estado": "DESCONOCIDO"}

    #valor  = datos.get("valor", payload)
    try:
        valor = datos.get("valor", payload)
    except AttributeError:
    valor = datos
    estado = datos.get("estado", "")
    hora   = datos.get("hora", datetime.now().strftime("%H:%M:%S"))

    if topic == topics["temperatura"]:
        estado_actual["temperatura"]       = valor
        estado_actual["temperatura_estado"] = estado
        estado_actual["ultima_actualizacion"] = hora
        db.guardar_lectura("temperatura", valor)

        # Si hay advertencia de temperatura → guardar evento
        if estado == "ADVERTENCIA_ALTA":
            db.guardar_evento("TEMP_ALTA", f"Temperatura: {valor}°C", "ADVERTENCIA")

    elif topic == topics["humedad_ambiente"]:
        estado_actual["humedad_ambiente"] = valor
        estado_actual["humedad_ambiente_estado"] = estado
        db.guardar_lectura("humedad_ambiente", valor)

    elif topic == topics["humedad_suelo_area1"]:
        estado_actual["humedad_suelo_area1"] = valor
        estado_actual["humedad_suelo_area1_estado"] = estado
        db.guardar_lectura("humedad_suelo_area1", valor)
        if estado == "SECO":
            db.guardar_evento("SUELO_SECO", f"Área 1 seca — valor: {valor}", "ADVERTENCIA")

    elif topic == topics["humedad_suelo_area2"]:
        estado_actual["humedad_suelo_area2"] = valor
        estado_actual["humedad_suelo_area2_estado"] = estado
        db.guardar_lectura("humedad_suelo_area2", valor)
        if estado == "SECO":
            db.guardar_evento("SUELO_SECO", f"Área 2 seca — valor: {valor}", "ADVERTENCIA")

    elif topic == topics["luz"]:
        estado_actual["luz"] = valor
        estado_actual["luz_estado"] = estado
        db.guardar_lectura("luz", valor)

    elif topic == topics["gas"]:
        estado_actual["gas"] = valor
        estado_actual["gas_estado"] = estado
        db.guardar_lectura("gas", valor)
        if estado == "GAS_EMERGENCIA":
            db.guardar_evento("GAS_EMERGENCIA", f"Gas peligroso: {valor}", "EMERGENCIA")
        elif estado == "GAS_ADVERTENCIA":
            db.guardar_evento("GAS_ADVERTENCIA", f"Gas elevado: {valor}", "ADVERTENCIA")

    elif topic == topics["estado_global"]:
        estado_actual["estado_global"] = datos.get("estado", payload)
        db.actualizar_estado_global(datos.get("estado", payload))
        db.guardar_evento("ESTADO_GLOBAL", f"Estado: {datos.get('estado', payload)}")

    elif topic == topics["riego_area1"]:
        estado_actual["riego"] = datos.get("estado", "OFF")

    elif topic == topics["ventilador"]:
        estado_actual["ventilador"] = datos.get("estado", "OFF")

    elif topic == topics["luces"]:
        estado_actual["luces"] = datos.get("estado", "OFF")

    elif topic == topics["alarma"]:
        estado_actual["alarma"] = datos.get("estado", "OFF")

    # Tiempo real al navegador
    if socketio_ref:
        socketio_ref.emit("actualizacion", estado_actual)


def publicar_comando(accion, valor):
    """Publica un comando desde el dashboard hacia la Raspberry Pi"""
    topics = Config.TOPICS
    mapa   = {
        "riego":      topics["riego"],
        "riego_area1":    topics["riego_area1"],
        "riego_area2":    topics["riego_area2"],
        "ventilador": topics["ventilador"],
        "luces":      topics["luces"],
        "alarma":     topics["alarma"],
        "remoto":     topics["control_remoto"],
    }

    if accion not in mapa:
        return False

    if not mqtt_client.is_connected():
        print(f"[MQTT] No se pudo enviar comando. Cliente desconectado: {accion}={valor}")
        return False

    topic = mapa[accion]
    resultado = mqtt_client.publish(topic, str(valor), qos=1)

    if resultado.rc != mqtt.MQTT_ERR_SUCCESS:
        print(
            f"[MQTT] Fallo publicando comando | "
            f"topic={topic} accion={accion} valor={valor} rc={resultado.rc}"
        )
        return False

    db.guardar_comando(accion, valor)
    print(f"Comando enviado | {topic} | {accion}: {valor}")
    return True


# Crear y configurar el cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

if Config.MQTT_USER:
    mqtt_client.username_pw_set(Config.MQTT_USER, Config.MQTT_PASSWORD)


def iniciar_mqtt():
    """Inicia la conexión MQTT en segundo plano"""
    try:
        mqtt_client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        mqtt_client.loop_start()   # corre en un hilo separado
        print(f"Conectando a broker: {Config.MQTT_BROKER}")
    except Exception as e:
        print(f"No se pudo conectar al broker MQTT: {e}")
        print("   El dashboard funcionará pero sin datos en tiempo real")
