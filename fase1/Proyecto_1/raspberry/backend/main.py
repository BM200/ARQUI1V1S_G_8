import os
import time
import csv
import serial
import threading
from datetime import datetime
from pymongo import MongoClient
import paho.mqtt.client as mqtt
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
try:
    import adafruit_dht
    import board
    DHT_DISPONIBLE = True
except ImportError:
    DHT_DISPONIBLE = False
    print("[DHT11] Librería adafruit_dht no disponible — temp/hum vendrán por MQTT.")

from config import *
from sensores import sensor_suelo, sensor_gas, sensor_luz

# ==========================================================
# PINES CORREGIDOS — LEDs de estado (no son relés)
# ==========================================================
LED_VERDE    = 5    # GPIO 5,  pin físico 29
LED_AMARILLO = 6    # GPIO 6,  pin físico 31
LED_ROJO     = 13   # GPIO 13, pin físico 33

# ==========================================================
# HELPER DE RELÉ (activo en LOW según config)
# rele(True)=encender, rele(False)=apagar
# ==========================================================
def rele(encender):
    if RELE_ACTIVO_EN_LOW:
        return GPIO.LOW if encender else GPIO.HIGH
    return GPIO.HIGH if encender else GPIO.LOW

# ==========================================================
# 1. INICIALIZACIÓN
# ==========================================================

# MongoDB
try:
    mongo_client = MongoClient(
        "mongodb+srv://Grupo8:Grupo8_12345%23@grupo8.4eccgif.mongodb.net/?appName=Grupo8",
        serverSelectionTimeoutMS=5000
    )
    db = mongo_client['invernadero_db']
    mongo_client.server_info()
    print("[BASE DE DATOS] Conexión con MongoDB establecida.")
except Exception as e:
    print(f"[BASE DE DATOS] Modo local (sin Atlas): {e}")
    db = None

# LCD I2C
try:
    lcd = CharLCD('PCF8574', 0x27, port=1, cols=16, rows=2)
    print("[PANTALLA] LCD inicializada en bus I2C.")
except Exception as e:
    print(f"[PANTALLA] Error LCD: {e}")
    lcd = None

# DHT11 local (Adafruit CircuitPython)
dht_sensor = None
if DHT_DISPONIBLE:
    try:
        dht_sensor = adafruit_dht.DHT11(board.D4)  # GPIO 4 = board.D4
        print("[DHT11] Sensor inicializado en GPIO 4.")
    except Exception as e:
        print(f"[DHT11] Error inicializando sensor: {e}")

# GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pines_in = [PIN_BOTON_MODO, PIN_BOTON_RIEGO, PIN_BOTON_LUCES, PIN_BOTON_BUZZER_RESET]

if PIN_ALARMA not in pines_in:
    pines_out = [PIN_BOMBA_AREA1, PIN_VENTILADOR, PIN_LEDS_BLANCOS_1,
                 LED_VERDE, LED_AMARILLO, LED_ROJO, PIN_ALARMA]
    alarma_disponible = True
else:
    pines_out = [PIN_BOMBA_AREA1, PIN_VENTILADOR, PIN_LEDS_BLANCOS_1,
                 LED_VERDE, LED_AMARILLO, LED_ROJO]
    alarma_disponible = False
    print("[ADVERTENCIA] PIN_ALARMA colisiona con entrada — alarma desactivada.")

GPIO.setup(pines_out, GPIO.OUT, initial=rele(False))
GPIO.setup(pines_in,  GPIO.IN,  pull_up_down=GPIO.PUD_UP)
# LEDs de estado son salida directa (no relé), asegurar LOW al inicio
GPIO.output([LED_VERDE, LED_AMARILLO, LED_ROJO], GPIO.LOW)

# Variables globales
estado_global      = "NORMAL"
modo_operacion     = "AUTOMATICO"
buffer_lecturas    = []
bloqueo_saturacion = False
temp_actual        = None
hum_actual         = None

# ==========================================================
# 2. MQTT
# ==========================================================

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT] Enlazado al Broker: {BROKER}")
        # Suscripción a DHT por si viene de otro proceso
        client.subscribe(TOPIC_DHT_TEMP)
        client.subscribe(TOPIC_DHT_HUM)
    else:
        print(f"[MQTT] Error de conexión: {reason_code}")

def on_message(client, userdata, msg):
    global temp_actual, hum_actual
    try:
        valor = float(msg.payload.decode('utf-8').strip())
        if msg.topic == TOPIC_DHT_TEMP:
            temp_actual = valor
        elif msg.topic == TOPIC_DHT_HUM:
            hum_actual = valor
    except Exception:
        pass

mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="backend_main_G8_P1"
)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# ==========================================================
# 3. LÓGICA DE ACTUADORES
# ==========================================================

def procesar_logica(datos):
    global estado_global, bloqueo_saturacion, modo_operacion

    temp_alta = (datos['temp'] is not None and datos['temp'] > UMBRAL_TEMP_ALTA)

    # EMERGENCIA — máxima prioridad
    if datos['e_gas'] == "GAS_EMERGENCIA" or temp_alta:
        GPIO.output(PIN_VENTILADOR, rele(True))
        mqtt_client.publish(TOPIC_VENTILADOR, "ON", qos=1)
        if datos['e_gas'] == "GAS_EMERGENCIA":
            estado_global = "EMERGENCIA"
            if alarma_disponible:
                GPIO.output(PIN_ALARMA, rele(True))
        return
    else:
        GPIO.output(PIN_VENTILADOR, rele(False))
        mqtt_client.publish(TOPIC_VENTILADOR, "OFF", qos=1)
        if alarma_disponible:
            GPIO.output(PIN_ALARMA, rele(False))

    # MODO MANUAL — el usuario controla, no tocamos actuadores
    if modo_operacion == "MANUAL":
        estado_global = "MODO_MANUAL"
        mqtt_client.publish(TOPIC_ESTADO_GLOBAL, estado_global, qos=1)
        return

    # RIEGO AUTOMÁTICO
    if datos['e_suelo'] == "SECO" and not bloqueo_saturacion:
        GPIO.output(PIN_BOMBA_AREA1, rele(True))
        estado_global = "RIEGO_ACTIVO"
        mqtt_client.publish(TOPIC_PUB_1, "ON", qos=1)
        print("[ACTUADOR] Bomba ENCENDIDA — suelo SECO")
    elif datos['e_suelo'] == "SATURADO":
        GPIO.output(PIN_BOMBA_AREA1, rele(False))
        bloqueo_saturacion = True
        mqtt_client.publish(TOPIC_PUB_1, "OFF", qos=1)
    else:
        GPIO.output(PIN_BOMBA_AREA1, rele(False))
        bloqueo_saturacion = False
        if estado_global == "RIEGO_ACTIVO":
            estado_global = "NORMAL"

    # ILUMINACIÓN AUTOMÁTICA
    if datos['e_luz'] == "OSCURO":
        GPIO.output(PIN_LEDS_BLANCOS_1, rele(True))
        mqtt_client.publish(TOPIC_ESTADO_LUZ_AREA1, "ENCENDIDAS", qos=1)
        print("[ACTUADOR] Luces ENCENDIDAS — oscuridad detectada")
    else:
        GPIO.output(PIN_LEDS_BLANCOS_1, rele(False))
        mqtt_client.publish(TOPIC_ESTADO_LUZ_AREA1, "APAGADAS", qos=1)

    # ESTADO GLOBAL
    if estado_global not in ("RIEGO_ACTIVO", "EMERGENCIA"):
        hay_advertencia = (datos['e_suelo'] == "SECO" or
                           datos['e_luz']   == "OSCURO" or temp_alta)
        estado_global = "ADVERTENCIA" if hay_advertencia else "NORMAL"

    mqtt_client.publish(TOPIC_ESTADO_GLOBAL, estado_global, qos=1)

# ==========================================================
# 4. INTERFAZ: LCD Y LEDS DE ESTADO
# ==========================================================

def actualizar_interfaz(datos):
    # LEDs de estado (salida directa, NO relé)
    GPIO.output([LED_VERDE, LED_AMARILLO, LED_ROJO], GPIO.LOW)
    if estado_global == "EMERGENCIA":
        GPIO.output(LED_ROJO, GPIO.HIGH)
    elif estado_global in ("RIEGO_ACTIVO", "ADVERTENCIA", "MODO_MANUAL"):
        GPIO.output(LED_AMARILLO, GPIO.HIGH)
    else:
        GPIO.output(LED_VERDE, GPIO.HIGH)

    # LCD — sin clear() para evitar parpadeo y errores I2C
    if lcd is not None:
        try:
            temp_str = f"{datos['temp']:.1f}" if datos['temp'] is not None else "--.-"
            hum_str  = f"{datos['hum']:.0f}"  if datos['hum']  is not None else "--"
            linea1 = f"T:{temp_str}C H:{hum_str}%"[:16].ljust(16)
            suelo_c = datos['e_suelo'][:4]
            gas_c   = datos['e_gas'].replace("GAS_", "")[:4]
            linea2  = f"S:{suelo_c} G:{gas_c}"[:16].ljust(16)
            lcd.cursor_pos = (0, 0)
            lcd.write_string(linea1)
            lcd.cursor_pos = (1, 0)
            lcd.write_string(linea2)
        except Exception as e:
            print(f"[LCD] Error: {e}")

# ==========================================================
# 5. PERSISTENCIA Y CSV ARM64
# ==========================================================

def manejar_datos(datos):
    global buffer_lecturas

    if db is not None:
        try:
            db.sensor_readings.insert_one({**datos, "fecha": datetime.now()})
        except Exception as e:
            print(f"[DATABASE] Error: {e}")

    if len(buffer_lecturas) < TOTAL_MUESTRAS_ARM64:
        lectura = [
            len(buffer_lecturas) + 1,
            datos['temp']  if datos['temp'] is not None else "",
            datos['hum']   if datos['hum']  is not None else "",
            datos['val_s1'],
            0,
            datos['val_luz'],
            datos['val_gas'],
            1 if GPIO.input(PIN_BOMBA_AREA1) == rele(True) else 0,
            0
        ]
        buffer_lecturas.append(lectura)

    if len(buffer_lecturas) == TOTAL_MUESTRAS_ARM64:
        try:
            ruta_csv = str(CSV_ARM64)
            os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
            with open(ruta_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID','TEMP','HUM_AIRE','HUM_SUELO_1','HUM_SUELO_2',
                                  'LUZ','GAS','RIEGO_1','RIEGO_2'])
                writer.writerows(buffer_lecturas)
            print(f"[ARM64] CSV generado en: {ruta_csv}")
        except Exception as e:
            print(f"[ARM64] Error CSV: {e}")
        buffer_lecturas = []

# ==========================================================
# 6. LECTURA DHT11 LOCAL
# ==========================================================

def leer_dht11():
    """Lee temperatura y humedad del DHT11 directamente en la Raspberry."""
    global temp_actual, hum_actual
    while True:
        if dht_sensor is not None:
            try:
                t = dht_sensor.temperature
                h = dht_sensor.humidity
                if t is not None and h is not None:
                    temp_actual = t
                    hum_actual  = h
                    mqtt_client.publish(TOPIC_DHT_TEMP, str(t), qos=1)
                    mqtt_client.publish(TOPIC_DHT_HUM,  str(h), qos=1)
            except Exception:
                pass  # DHT11 falla ocasionalmente, ignorar y reintentar
        time.sleep(3)  # DHT11 necesita mínimo 2s entre lecturas

# ==========================================================
# 7. HILOS PRINCIPALES
# ==========================================================

def loop_principal():
    try:
        ser = serial.Serial(PUERTO_SERIAL, VELOCIDAD, timeout=1)
        print(f"[SERIAL] Canal abierto en: {PUERTO_SERIAL}")
    except Exception as e:
        print(f"[SERIAL] FATAL: {e}")
        return

    ser.reset_input_buffer()

    while True:
        try:
            if ser.in_waiting > 0:
                linea  = ser.readline().decode('utf-8', errors='ignore').strip()
                valores = linea.split(',')
                if len(valores) == NUM_VALORES:
                    _, _, e_gas   = sensor_gas.procesar(int(valores[IDX_GAS]))
                    _, _, e_suelo = sensor_suelo.procesar(int(valores[IDX_SUELO1]), 1)
                    _, _, e_luz   = sensor_luz.procesar(int(valores[IDX_LDR]))

                    datos = {
                        'temp':    temp_actual,
                        'hum':     hum_actual,
                        'val_gas': int(valores[IDX_GAS]),
                        'e_gas':   e_gas,
                        'val_s1':  int(valores[IDX_SUELO1]),
                        'e_suelo': e_suelo,
                        'val_luz': int(valores[IDX_LDR]),
                        'e_luz':   e_luz,
                    }

                    print(f"[DATOS] T={datos['temp']} H={datos['hum']} "
                          f"suelo={datos['val_s1']}({datos['e_suelo']}) "
                          f"gas={datos['val_gas']}({datos['e_gas']}) "
                          f"luz={datos['val_luz']}({datos['e_luz']}) "
                          f"modo={modo_operacion} estado={estado_global}")

                    procesar_logica(datos)
                    actualizar_interfaz(datos)
                    manejar_datos(datos)

                    # Publicar sensores individualmente en MQTT
                    mqtt_client.publish(TOPIC_GAS,         str(datos['val_gas']), qos=1)
                    mqtt_client.publish(TOPIC_SUELO_AREA1, str(datos['val_s1']),  qos=1)
                    mqtt_client.publish(TOPIC_LDR,         str(datos['val_luz']), qos=1)
                    mqtt_client.publish(TOPIC_MODO_LUZ,    modo_operacion,        qos=1)

        except Exception as e:
            print(f"[CORE LOOP] Error: {e}")

        time.sleep(INTERVALO_LECTURA_SEG)


def _cb_boton_modo(channel):
    global modo_operacion
    modo_operacion = "MANUAL" if modo_operacion == "AUTOMATICO" else "AUTOMATICO"
    print(f"[BOTÓN] Modo → {modo_operacion}")
    mqtt_client.publish(TOPIC_MODO_LUZ, modo_operacion, qos=1)

def _cb_boton_riego(channel):
    if modo_operacion == "MANUAL":
        encendida = GPIO.input(PIN_BOMBA_AREA1) == rele(True)
        GPIO.output(PIN_BOMBA_AREA1, rele(not encendida))
        print(f"[BOTÓN] Bomba → {'ON' if not encendida else 'OFF'}")
        mqtt_client.publish(TOPIC_PUB_1, "ON" if not encendida else "OFF", qos=1)

def _cb_boton_luces(channel):
    encendida = GPIO.input(PIN_LEDS_BLANCOS_1) == rele(True)
    GPIO.output(PIN_LEDS_BLANCOS_1, rele(not encendida))
    print(f"[BOTÓN] Luces → {'ON' if not encendida else 'OFF'}")
    mqtt_client.publish(TOPIC_ESTADO_LUZ_AREA1,
                        "ENCENDIDAS" if not encendida else "APAGADAS", qos=1)

def monitoreo_botones():
    print("[BOTONES] Registrando interrupciones por flanco.")
    for pin in [PIN_BOTON_MODO, PIN_BOTON_RIEGO, PIN_BOTON_LUCES]:
        try:
            GPIO.remove_event_detect(pin)
        except Exception:
            pass
    try:
        GPIO.add_event_detect(PIN_BOTON_MODO,  GPIO.FALLING,
                              callback=_cb_boton_modo,  bouncetime=300)
        GPIO.add_event_detect(PIN_BOTON_RIEGO, GPIO.FALLING,
                              callback=_cb_boton_riego, bouncetime=300)
        GPIO.add_event_detect(PIN_BOTON_LUCES, GPIO.FALLING,
                              callback=_cb_boton_luces, bouncetime=300)
        print("[BOTONES] Interrupciones registradas correctamente.")
    except Exception as e:
        print(f"[BOTONES] Error: {e} — botones físicos desactivados.")
    while True:
        time.sleep(1)

# ==========================================================
# 8. ARRANQUE
# ==========================================================

if __name__ == "__main__":
    print("==========================================================")
    print(" Invernadero Inteligente IoT — Grupo 8 / Central          ")
    print("==========================================================")

    try:
        mqtt_client.connect(BROKER, PORT, 60)
        mqtt_client.loop_start()
        print(f"[MQTT] Conectando al Broker: {BROKER}")
    except Exception as e:
        print(f"[MQTT] Sin broker activo: {e}")

    threading.Thread(target=loop_principal,    daemon=True).start()
    threading.Thread(target=monitoreo_botones, daemon=True).start()
    threading.Thread(target=leer_dht11,        daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCierre manual detectado...")
    finally:
        print("Apagando actuadores por seguridad...")
        try:
            GPIO.output(pines_out, rele(False))
            GPIO.output([LED_VERDE, LED_AMARILLO, LED_ROJO], GPIO.LOW)
            GPIO.cleanup()
        except Exception:
            pass
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("[APAGADO] Sistema cerrado correctamente.")
