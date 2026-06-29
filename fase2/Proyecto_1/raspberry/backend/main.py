import sys
import os
import time
import json
import threading
import serial
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import certifi

BACKEND_DIR   = os.path.dirname(os.path.abspath(__file__))
PROYECTO_DIR  = os.path.abspath(os.path.join(BACKEND_DIR, '..'))
DASHBOARD_DIR = os.path.join(PROYECTO_DIR, 'invernadero_dashboard')

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, DASHBOARD_DIR)


load_dotenv(os.path.join(PROYECTO_DIR, '.env'))

from config import (
    BROKER, PORT, KEEPALIVE,
    CLIENT_ID_MAIN,
    TOPIC_SUELO_AREA1, TOPIC_SUELO_AREA2,
    TOPIC_LDR, TOPIC_GAS,
    TOPIC_DHT_TEMP, TOPIC_DHT_HUM,
    TOPIC_RIEGO_AREA1, TOPIC_VENTILADOR,
    TOPIC_LUCES, TOPIC_ALARMA,
    TOPIC_CONTROL_MANUAL, TOPIC_ESTADO_GLOBAL,
    PUERTO_SERIAL, VELOCIDAD, INTERVALO_LECTURA_SEG,
    IDX_GAS, IDX_SUELO1, IDX_SUELO2, IDX_LDR,
    UMBRAL_SECO, UMBRAL_SATURADO, UMBRAL_LUZ_BAJA,
    UMBRAL_GAS_NORMAL, UMBRAL_GAS_ALERTA, UMBRAL_TEMP_ALTA,
    FLASK_HOST, FLASK_PORT,
    CSV_ARM64
)

# Sensores
from sensores.suelo import set_db as suelo_set_db, set_cliente_mqtt as suelo_set_mqtt
from sensores.gas import (
    set_db as gas_set_db, set_cliente_mqtt as gas_set_mqtt,
    reset_emergencia, apagar_todo as gas_apagar, get_estado as gas_get_estado
)
from sensores.ldr import (
    set_db as ldr_set_db, set_cliente_mqtt as ldr_set_mqtt,
    encender_luces_manual, apagar_luces_manual, set_modo_luces
)
from sensores.dht11 import (
    iniciar as dht_iniciar, detener as dht_detener, set_db as dht_set_db, 
    set_cliente_mqtt as dht_set_mqtt, set_callback_temp_alta, get_ultima_lectura as dht_get_lectura
)
from sensores.lcd import iniciar as lcd_iniciar, detener as lcd_detener
from sensores.botones import configurar as configurar_botones, set_cliente_mqtt as botones_set_mqtt

# Actuadores
from actuadores.riego import (
    activar_bomba, activar_ventilador, cancelar_bomba, cancelar_ventilador,
    apagar_todo, limpiar_gpio, set_db as riego_set_db, set_cliente_mqtt as riego_set_mqtt
)

from arm64_bridge import run_live_engine


MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[ERROR] MONGO_URI no está en el .env — verificá el archivo")
    sys.exit(1)

mongo = MongoClient(MONGO_URI)
db    = mongo[os.getenv("MONGO_DB_NAME", "invernadero_g8")]
print("[MONGO] Conectado a Atlas")

# Db en todos los módulos
suelo_set_db(db)
gas_set_db(db)
ldr_set_db(db)
dht_set_db(db)
riego_set_db(db)

mongo = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

modo_ventilador = "AUTOMATICO"
modo_luces      = "AUTOMATICO"
CSV_ARM64_HEADER = "TEMP,HUM_AIRE,SOIL1,SOIL2,LUZ,GAS"

def on_connect(client, userdata, flags, rc, props=None):
    if rc == 0:
        print("[MQTT] Conectado al broker")
        client.subscribe(TOPIC_RIEGO_AREA1)
        client.subscribe(TOPIC_VENTILADOR)
        client.subscribe(TOPIC_LUCES)
        client.subscribe(TOPIC_ALARMA)
        client.subscribe(TOPIC_CONTROL_MANUAL)
    else:
        print(f"[MQTT] Error de conexión: {rc}")

def on_message(client, userdata, msg):
    global modo_ventilador, modo_luces
    try:
        contenido = msg.payload.decode().strip()
        topic     = msg.topic

        try:
            datos   = json.loads(contenido)
            comando = datos.get("comando", "")
        except json.JSONDecodeError:
            if contenido in ["ON", "ENCENDER", "1"]:
                comando = "ENCENDER"
            elif contenido in ["OFF", "APAGAR", "0"]:
                comando = "APAGAR"
            else:
                comando = contenido
            datos = {"comando": comando}

        if topic == TOPIC_RIEGO_AREA1:
            if comando == "ENCENDER":
                activar_bomba(origen="DASHBOARD")
            elif comando == "APAGAR":
                cancelar_bomba()

        elif topic == TOPIC_VENTILADOR:
            if comando == "ENCENDER":
                activar_ventilador(origen="DASHBOARD")
            elif comando == "APAGAR":
                cancelar_ventilador()

        elif topic == TOPIC_LUCES:
            if comando == "ENCENDER":
                encender_luces_manual()
            elif comando == "APAGAR":
                apagar_luces_manual()

        elif topic == TOPIC_ALARMA:
            if comando in ["RESET", "APAGAR"]:
                reset_emergencia()

        elif topic == TOPIC_CONTROL_MANUAL:
            modo = datos.get("modo", contenido)
            if modo in ["AUTOMATICO", "MANUAL"]:
                modo_ventilador = modo
                modo_luces      = modo
                set_modo_luces(modo)
                print(f"[MAIN] Modo cambiado a: {modo}")

    except Exception as e:
        print(f"[MQTT] Error en on_message: {e}")

        
cliente_mqtt = mqtt.Client(
    client_id=CLIENT_ID_MAIN,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
cliente_mqtt.on_connect = on_connect
cliente_mqtt.on_message = on_message
cliente_mqtt.connect(BROKER, PORT, KEEPALIVE)
cliente_mqtt.loop_start()

# Cliente MQTT en todos los módulos
suelo_set_mqtt(cliente_mqtt)
gas_set_mqtt(cliente_mqtt)
ldr_set_mqtt(cliente_mqtt)
dht_set_mqtt(cliente_mqtt)
riego_set_mqtt(cliente_mqtt)
botones_set_mqtt(cliente_mqtt)


set_callback_temp_alta(lambda *args, **kwargs: None)

# DHT11 y LCD
lcd_iniciar()
dht_iniciar()

# Botones físicos
configurar_botones(
    activar_bomba_fn      = activar_bomba,
    activar_ventilador_fn = activar_ventilador,
    toggle_luces_fn       = encender_luces_manual,
    reset_gas_fn          = reset_emergencia
)

# Conectar con arduino
def conectar_serial():
    try:
        ser = serial.Serial(PUERTO_SERIAL, VELOCIDAD, timeout=2)
        print(f"[SERIAL] Arduino conectado en {PUERTO_SERIAL}")
        return ser
    except Exception as e:
        print(f"[SERIAL] No se pudo abrir {PUERTO_SERIAL}: {e}")
        print("[SERIAL] Continuando sin Arduino — verificá el cable USB")
        return None


ACCIONES_PERMITIDAS = {
    "ALARM_ON",
    "RIEGO_1_ON",
    "RIEGO_2_ON",
    "LIGHT_ON",
    "FAN_ON",
    "LED_GREEN",
    "NO_ACTION",
}


def obtener_modo_actual():
    # esto convierte el modo actual a numero para arm64
    if modo_ventilador == "MANUAL" or modo_luces == "MANUAL":
        return 1
    return 0


def obtener_lectura_dht():
    # esto obtiene la ultima lectura disponible del dht11
    lectura = dht_get_lectura() or {}
    temp = lectura.get("temperatura") or 0
    hum = lectura.get("humedad_ambiente") or 0
    return int(temp), int(hum)


def construir_lectura_completa(gas, suelo1, suelo2, ldr):
    # esto arma la lectura que espera arm64
    temp, hum = obtener_lectura_dht()
    return {
        "temp": temp,
        "hum": hum,
        "val_s1": int(suelo1),
        "val_s2": int(suelo2),
        "val_luz": int(ldr),
        "val_gas": int(gas),
        "modo": obtener_modo_actual(),
    }


def normalizar_decision_arm64(decision):
    # esto normaliza claves para guardar y validar
    decision = decision or {}
    status = decision.get("status") or decision.get("STATUS") or "ERROR"
    action = decision.get("action") or decision.get("ACTION")
    return {
        "status": status,
        "action": action,
        "target": decision.get("target") or decision.get("TARGET"),
        "risk": decision.get("risk") or decision.get("RISK"),
        "reason": decision.get("reason") or decision.get("REASON"),
        "value": decision.get("value") or decision.get("VALUE"),
        "indicator": decision.get("indicator") or decision.get("INDICATOR"),
        "error": decision.get("error") or decision.get("ERROR"),
        "detail": decision.get("detail") or decision.get("DETAIL"),
    }


def ejecutar_accion_arm64(action, datos_lectura):
    # esto aplica solo acciones aprobadas por arm64
    if action not in ACCIONES_PERMITIDAS:
        return "NO_EJECUTADA", "accion no permitida", False

    if action == "NO_ACTION":
        return "NO_ACTION", "sin accion requerida", False

    if action == "RIEGO_1_ON":
        activar_bomba(origen="ARM64_RIEGO_1")
        return action, "bomba area 1 activada", True

    if action == "RIEGO_2_ON":
        activar_bomba(origen="ARM64_RIEGO_2")
        return action, "bomba area 2 activada", True

    if action == "LIGHT_ON":
        encender_luces_manual()
        return action, "luces activadas", True

    if action == "FAN_ON":
        activar_ventilador(segundos=20, origen="ARM64")
        return action, "ventilador activado", True

    if action == "ALARM_ON":
        return action, "alarma decidida por ARM64; sin activar logica Python", False

    if action == "LED_GREEN":
        reset_emergencia()
        return action, "estado normal aplicado", True

    return "NO_EJECUTADA", "accion sin manejador", False


def guardar_lectura_mongo(datos_lectura, decision_arm64, accion, resultado, gpio_aplicado):
    # esto guarda la lectura completa para dashboard y auditoria
    ahora = datetime.now()
    documento = {
        "timestamp": ahora,
        "fecha": ahora,
        "temp": datos_lectura["temp"],
        "hum": datos_lectura["hum"],
        "val_s1": datos_lectura["val_s1"],
        "val_s2": datos_lectura["val_s2"],
        "val_luz": datos_lectura["val_luz"],
        "val_gas": datos_lectura["val_gas"],
        "modo": datos_lectura["modo"],
        "decision_arm64": decision_arm64,
        "accion_ejecutada": accion,
        "resultado_actuador": resultado,
        "gpio_aplicado": gpio_aplicado,
        "status_arm64": decision_arm64.get("status"),
    }
    db["sensor_readings"].insert_one(documento)
    return documento


def guardar_lectura_csv(datos_lectura):
    # esto agrega la lectura real al csv usado por arm64
    CSV_ARM64.parent.mkdir(parents=True, exist_ok=True)
    crear_header = not CSV_ARM64.exists() or CSV_ARM64.stat().st_size == 0
    modo_apertura = "a"

    if crear_header:
        print(f"[ARM64 CSV] Creando CSV real: {CSV_ARM64}")

    if not crear_header:
        with CSV_ARM64.open("r", encoding="utf-8-sig") as archivo:
            primera_linea = archivo.readline().strip()
        if primera_linea != CSV_ARM64_HEADER:
            crear_header = True
            modo_apertura = "w"
            print(
                "[ARM64 CSV] Encabezado inválido o viejo detectado. "
                f"Esperado={CSV_ARM64_HEADER!r} Encontrado={primera_linea!r}. "
                "Regenerando CSV con lecturas reales."
            )

    with CSV_ARM64.open(modo_apertura, encoding="utf-8") as archivo:
        if crear_header:
            archivo.write(f"{CSV_ARM64_HEADER}\n")
        archivo.write(
            f"{datos_lectura['temp']},"
            f"{datos_lectura['hum']},"
            f"{datos_lectura['val_s1']},"
            f"{datos_lectura['val_s2']},"
            f"{datos_lectura['val_luz']},"
            f"{datos_lectura['val_gas']}\n"
        )


def clasificar_suelo(valor):
    valor = int(valor)
    if valor >= UMBRAL_SECO:
        return "SECO"
    if valor <= UMBRAL_SATURADO:
        return "SATURADO"
    return "NORMAL"


def clasificar_luz(valor):
    valor = int(valor)
    if valor < UMBRAL_LUZ_BAJA:
        return "OSCURO"
    return "LUZ"


def clasificar_gas(valor):
    valor = int(valor)
    if valor < UMBRAL_GAS_NORMAL:
        return "GAS_NORMAL"
    if valor <= UMBRAL_GAS_ALERTA:
        return "GAS_ADVERTENCIA"
    return "GAS_EMERGENCIA"


def publicar_sensor_mqtt(topic, sensor, valor, estado, hora=None):
    hora = hora or datetime.now().strftime("%H:%M:%S")
    payload = json.dumps({
        "sensor": sensor,
        "valor": int(valor),
        "estado": estado,
        "hora": hora,
    })
    cliente_mqtt.publish(topic, payload, qos=1)


def publicar_sensores_serial(datos_lectura):
    hora = datetime.now().strftime("%H:%M:%S")
    publicar_sensor_mqtt(
        TOPIC_SUELO_AREA1,
        "suelo_area1",
        datos_lectura["val_s1"],
        clasificar_suelo(datos_lectura["val_s1"]),
        hora,
    )
    publicar_sensor_mqtt(
        TOPIC_SUELO_AREA2,
        "suelo_area2",
        datos_lectura["val_s2"],
        clasificar_suelo(datos_lectura["val_s2"]),
        hora,
    )
    publicar_sensor_mqtt(
        TOPIC_LDR,
        "luz",
        datos_lectura["val_luz"],
        clasificar_luz(datos_lectura["val_luz"]),
        hora,
    )
    publicar_sensor_mqtt(
        TOPIC_GAS,
        "gas",
        datos_lectura["val_gas"],
        clasificar_gas(datos_lectura["val_gas"]),
        hora,
    )


def procesar_lectura_arm64(datos_lectura):
    # esto envia la lectura real al motor arm64
    decision_raw = run_live_engine(datos_lectura)
    decision = normalizar_decision_arm64(decision_raw)
    status = decision.get("status")
    action = decision.get("action")

    if status == "ERROR":
        print(f"[ARM64] Error: {decision.get('detail') or decision.get('error')}")
        guardar_lectura_mongo(
            datos_lectura,
            decision,
            "NO_EJECUTADA",
            decision.get("detail") or "error arm64",
            False,
        )
        guardar_lectura_csv(datos_lectura)
        return

    accion, resultado, gpio_aplicado = ejecutar_accion_arm64(action, datos_lectura)
    guardar_lectura_mongo(datos_lectura, decision, accion, resultado, gpio_aplicado)
    guardar_lectura_csv(datos_lectura)
    print(f"[ARM64] ACTION={action} STATUS={status} GPIO={gpio_aplicado}")


def bucle_principal():
    ser = conectar_serial()
    print("[MAIN] Sistema iniciado. Ctrl+C para detener.\n")

    while True:
        if ser:
            try:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()

                if linea and ',' in linea:
                    partes = linea.split(',')

                    if len(partes) == 4:
                        gas    = int(partes[IDX_GAS])
                        suelo1 = int(partes[IDX_SUELO1])
                        suelo2 = int(partes[IDX_SUELO2])
                        ldr    = int(partes[IDX_LDR])

                        datos_lectura = construir_lectura_completa(
                            gas=gas,
                            suelo1=suelo1,
                            suelo2=suelo2,
                            ldr=ldr,
                        )
                        publicar_sensores_serial(datos_lectura)
                        procesar_lectura_arm64(datos_lectura)

            except ValueError as e:
                print(f"[SERIAL] Valor inválido: {e}")
            except Exception as e:
                print(f"[SERIAL] Error: {e}")
                time.sleep(1)

        
        time.sleep(INTERVALO_LECTURA_SEG)

if __name__ == "__main__":
    try:
        bucle_principal()
    except KeyboardInterrupt:
        print("\n[MAIN] Deteniendo sistema...")
    finally:
        print("[MAIN] Apagando actuadores...")
        apagar_todo()
        gas_apagar()
        limpiar_gpio()
        dht_detener()
        lcd_detener()
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()
        mongo.close()
        print("[MAIN] Sistema detenido de forma segura.")
