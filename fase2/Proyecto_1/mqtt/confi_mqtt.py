# Broker MQTT.
BROKER = "broker.emqx.io"

# Puerto TCP del broker.
PORT = 1883

#Nombre del proyecto
PROJECT_NAME = "Arqui1_G8_P1"

# Nombre base del proyecto.
BASE_TOPIC = "Invernadero/G8/P1"

# Topics principales del sistema.
TOPICS = {
    # Sensores
    "temperatura": f"{BASE_TOPIC}/sensores/temperatura",
    "humedad_ambiente": f"{BASE_TOPIC}/sensores/humedad_ambiente",
    "humedad_suelo_area1": f"{BASE_TOPIC}/sensores/humedad_suelo_area1",
    "humedad_suelo_area2": f"{BASE_TOPIC}/sensores/humedad_suelo_area2",
    "luz": f"{BASE_TOPIC}/sensores/luz",
    "gas": f"{BASE_TOPIC}/sensores/gas",

    # Actuadores
    "riego": f"{BASE_TOPIC}/actuadores/riego",
    "riego_area1": f"{BASE_TOPIC}/actuadores/riego_area1",
    "riego_area2": f"{BASE_TOPIC}/actuadores/riego_area2",
    "ventilador": f"{BASE_TOPIC}/actuadores/ventilador",
    "luces": f"{BASE_TOPIC}/actuadores/luces",
    "alarma": f"{BASE_TOPIC}/actuadores/alarma",

    # Estado
    "estado_global": f"{BASE_TOPIC}/estado/global",

    #control
    "control_remoto": f"{BASE_TOPIC}/control/remoto",
    "control_manual": f"{BASE_TOPIC}/control/manual",
}