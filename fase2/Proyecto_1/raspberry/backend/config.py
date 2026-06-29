from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
RASPBERRY_DIR = BACKEND_DIR.parent
ARM64_DIR = RASPBERRY_DIR / "arm64"
ARM64_BUILD_DIR = ARM64_DIR / "build"
CSV_ARM64 = ARM64_DIR / "lecturas.csv"


# MQTT

BROKER = "broker.emqx.io"
PORT = 1883
KEEPALIVE = 60
PROJECT_NAME = "Arqui1_G8_P1"

CLIENT_ID_MAIN = "backend_main_G8_P1"
CLIENT_ID_GESTOR = "gestor_datos_G8_P1"
CLIENT_ID_PUBLICADOR = "publicador_sensores_G8_P1"
CLIENT_ID_ACTUADOR = "actuadores_G8_P1"
CLIENT_ID_DHT = "sensor_dht11_G8_P1"

# TÓPICOS 
TOPIC_DHT_TEMP = "invernadero/G8/P1/sensores/temperatura"
TOPIC_DHT_HUM = "invernadero/G8/P1/sensores/humedad_ambiente"
TOPIC_SUELO_AREA1 = "invernadero/G8/P1/sensores/humedad_suelo_area1"
TOPIC_SUELO_AREA2 = "invernadero/G8/P1/sensores/humedad_suelo_area2"
TOPIC_LDR = "invernadero/G8/P1/sensores/luz"
TOPIC_GAS = "invernadero/G8/P1/sensores/gas"

TOPIC_RIEGO_GLOBAL = "invernadero/G8/P1/actuadores/riego"
TOPIC_RIEGO_AREA1 = "invernadero/G8/P1/actuadores/riego_area1"
TOPIC_RIEGO_AREA2 = "invernadero/G8/P1/actuadores/riego_area2"
TOPIC_VENTILADOR = "invernadero/G8/P1/actuadores/ventilador"
TOPIC_LUCES = "invernadero/G8/P1/actuadores/luces"
TOPIC_ALARMA = "invernadero/G8/P1/actuadores/alarma"

TOPIC_ESTADO_GLOBAL = "invernadero/G8/P1/estado/global"
TOPIC_CONTROL_REMOTO = "invernadero/G8/P1/control/remoto"
TOPIC_CONTROL_MANUAL = "invernadero/G8/P1/control/manual"

TOPIC_PUB_GLOBAL = TOPIC_RIEGO_GLOBAL
TOPIC_PUB_1 = TOPIC_RIEGO_AREA1
TOPIC_PUB_2 = TOPIC_RIEGO_AREA2
TOPIC_MODO_LUZ = TOPIC_CONTROL_MANUAL
TOPIC_CONTROL_LUZ = TOPIC_LUCES
TOPIC_ESTADO_LUZ_AREA1 = TOPIC_LUCES
TOPIC_ESTADO_LUZ_AREA2 = TOPIC_LUCES

SENSOR_TOPICS = {
    "temperatura": TOPIC_DHT_TEMP,
    "humedad_ambiente": TOPIC_DHT_HUM,
    "humedad_suelo_area1": TOPIC_SUELO_AREA1,
    "humedad_suelo_area2": TOPIC_SUELO_AREA2,
    "luz": TOPIC_LDR,
    "gas": TOPIC_GAS,
}

# Orden usado para crear lecturas.csv
CSV_HEADERS = [
    "muestra",
    "temperatura",
    "humedad_ambiente",
    "humedad_suelo_area1",
    "humedad_suelo_area2",
    "luz",
    "gas",
]


ARM64_SENSOR_COLUMNS = {
    "temperatura": 2,
    "humedad_ambiente": 3,
    "humedad_suelo_area1": 4,
    "humedad_suelo_area2": 5,
    "luz": 6,
    "gas": 7,
}

MODULOS_ARM64 = {
    1: "modulo_1_media",
    2: "modulo_2_varianza",
    3: "modulo_3_anomalias",
    4: "modulo_4_prediccion",
    5: "modulo_5_tendencia",
}

MODULOS_A_EJECUTAR = [1, 2, 3, 4, 5]
SENSORES_A_PROCESAR_ARM64 = list(ARM64_SENSOR_COLUMNS.keys())
TOTAL_MUESTRAS_ARM64 = 30
ARM64_TIMEOUT_SEG = 10

# FLASK

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False

# SERIAL / ARDUINO

PUERTO_SERIAL = "/dev/ttyACM0"
VELOCIDAD = 9600
NUM_VALORES = 4
INTERVALO_LECTURA_SEG = 2
IDX_GAS    = 0
IDX_SUELO1 = 1
IDX_SUELO2 = 2
IDX_LDR    = 3


# UMBRALES DE SENSORES

UMBRAL_SECO = 700
UMBRAL_NORMAL = 400
UMBRAL_SATURADO = 300
UMBRAL_LUZ_BAJA = 300
# True: valor alto del LDR significa oscuro. False: valor bajo significa oscuro.
LDR_OSCURO_EN_VALOR_ALTO = True
UMBRAL_GAS_NORMAL = 200
UMBRAL_GAS_ALERTA = 400
UMBRAL_TEMP_ALTA = 30.0


# GPIO RASPBERRY PI
PIN_BOMBA_AREA1 = 20
PIN_BOMBA_AREA2 = None
PIN_BOMBA = PIN_BOMBA_AREA1
PIN_VENTILADOR = 16 # OJITO
PIN_DHT11 = 4
PIN_LEDS_BLANCOS_1 = 12
PIN_LEDS_BLANCOS_2 = 26
PIN_ALARMA = 19

LED_VERDE = 5
LED_AMARILLO = 6
LED_ROJO = 13

PIN_BOTON_MODO        = 24
PIN_BOTON_RIEGO       = 18
PIN_BOTON_LUCES       = 9
PIN_BOTON_BUZZER_RESET = 21

DURACION_RIEGO = 5
PAUSA_MINIMA   = 5

#RELE_ACTIVO_EN_LOW = False
RELE_ACTIVO_EN_LOW = True

SUELO_UMBRAL_SECO = UMBRAL_SECO
SUELO_UMBRAL_SATURADO = UMBRAL_SATURADO
LUZ_UMBRAL_OSCURIDAD = UMBRAL_LUZ_BAJA
