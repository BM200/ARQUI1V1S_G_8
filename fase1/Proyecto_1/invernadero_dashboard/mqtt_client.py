# mqtt_client.py
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
        print("✅ Conectado al broker MQTT")
        # Suscribirse a todos los topics de sensores
        for topic in Config.TOPICS.values():
            client.subscribe(topic)
            print(f"   Suscrito a: {topic}")
    else:
        print(f"❌ Error al conectar al broker MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    """Se ejecuta cada vez que llega un mensaje MQTT"""
    topic   = msg.topic
    payload = msg.payload.decode("utf-8").strip()
    topics  = Config.TOPICS

    print(f"📨 MQTT recibido | {topic}: {payload}")

    # Actualizar estado según el topic recibido
    if topic == topics["temperatura"]:
        estado_actual["temperatura"] = payload
        estado_actual["ultima_actualizacion"] = datetime.now().strftime("%H:%M:%S")
        db.guardar_lectura("temperatura", payload)

    elif topic == topics["humedad_ambiente"]:
        estado_actual["humedad_ambiente"] = payload
        db.guardar_lectura("humedad_ambiente", payload)

    elif topic == topics["humedad_suelo_area1"]:
        estado_actual["humedad_suelo_area1"] = payload
        db.guardar_lectura("humedad_suelo_area1", payload)

    elif topic == topics["humedad_suelo_area2"]:
        estado_actual["humedad_suelo_area2"] = payload
        db.guardar_lectura("humedad_suelo_area2", payload)

    elif topic == topics["luz"]:
        estado_actual["luz"] = payload
        db.guardar_lectura("luz", payload)

    elif topic == topics["gas"]:
        try:
            datos_gas = json.loads(payload)
            valor_gas = datos_gas["valor"]
            estado_actual["gas"] = valor_gas

            db.guardar_lectura(
                "gas",
                valor_gas
            )

            if valor_gas > 300:
                db.guardar_evento(
                    "GAS_ALTO",
                    f"Nivel de gas: {valor_gas}",
                    "EMERGENCIA"
                )

        except Exception as e:
            print("Error procesando gas:", e)

    elif topic == topics["estado_global"]:
        estado_actual["estado_global"] = payload
        db.actualizar_estado_global(payload)
        db.guardar_evento("ESTADO_GLOBAL", f"Estado cambió a: {payload}")

    # Enviar actualización al navegador en tiempo real
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

    if accion in mapa:
        mqtt_client.publish(mapa[accion], str(valor))
        db.guardar_comando(accion, valor)
        print(f"📤 Comando enviado | {accion}: {valor}")
        return True
    return False


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
        print(f"🔌 Conectando a broker: {Config.MQTT_BROKER}")
    except Exception as e:
        print(f"⚠️  No se pudo conectar al broker MQTT: {e}")
        print("   El dashboard funcionará pero sin datos en tiempo real")

