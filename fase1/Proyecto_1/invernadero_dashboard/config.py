# config.py
# Aquí van todas las configuraciones del sistema

class Config:
    # --- MQTT ---
    # Reemplaza estos valores cuando tu compañero te los dé
    MQTT_BROKER   = "broker.emqx.io"   # broker público de prueba por ahora
    MQTT_PORT     = 1883
    MQTT_USER     = ""                    # dejar vacío si no hay usuario
    MQTT_PASSWORD = ""

    # --- MongoDB Atlas ---
    # cadena como:
    # "mongodb+srv://usuario:contraseña@cluster.mongodb.net/"
    MONGO_URI  = "mongodb+srv://Grupo8:Grupo8_12345%23@grupo8.4eccgif.mongodb.net/?appName=Grupo8"  # local por ahora
    MONGO_DB   = "P1_G8_ARQUI1"

   # Nombre base del proyecto.
    BASE_TOPIC = "invernadero/G8/P1"

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