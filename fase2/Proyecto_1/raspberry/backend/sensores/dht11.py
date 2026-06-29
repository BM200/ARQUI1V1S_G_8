import threading
import json
import board
import adafruit_dht
from datetime import datetime
from sensores import lcd

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    PIN_DHT11,
    TOPIC_DHT_TEMP, TOPIC_DHT_HUM, TOPIC_ESTADO_GLOBAL,
    UMBRAL_TEMP_ALTA,
    INTERVALO_LECTURA_SEG
)


sensor_dht = adafruit_dht.DHT11(board.D4)

# --- Estado interno ---
_ultima_temp     = 0.0
_ultima_hum      = 0.0
_estado_temp     = "NORMAL"    # NORMAL / ADVERTENCIA
_estado_hum      = "NORMAL"    # NORMAL / HUMEDAD_BAJA / HUMEDAD_ALTA
_timer_lectura   = None

# Umbrales 
TEMP_NORMAL_MAX  = UMBRAL_TEMP_ALTA   # 30.0 °C de config.py
TEMP_NORMAL_MIN  = 15.0
HUM_NORMAL_MIN   = 40.0
HUM_NORMAL_MAX   = 80.0


_db              = None
_cliente_mqtt    = None
_cb_temp_alta    = None   # callback para activar ventilador

def set_db(db):
    global _db
    _db = db

def set_cliente_mqtt(cliente):
    global _cliente_mqtt
    _cliente_mqtt = cliente

def set_callback_temp_alta(fn):
    """
    main.py inyecta aquí la función activar_ventilador().
    Así dht11.py no importa riego.py directamente — sin circular imports.
    """
    global _cb_temp_alta
    _cb_temp_alta = fn


def _publicar(topic, payload: dict):
    if _cliente_mqtt:
        _cliente_mqtt.publish(topic, json.dumps(payload), qos=1)
    print(f"[DHT11] {topic} → {payload}")

def _registrar(sensor, valor, estado, extra=None):
    if _db is None:
        return
    doc = {
        "sensor": sensor,
        "valor":  valor,
        "estado": estado,
        "fecha":  datetime.now()
    }
    if extra:
        doc.update(extra)
    _db["sensor_logs"].insert_one(doc)

def _clasificar_temp(temp):
    if temp > TEMP_NORMAL_MAX:
        return "ADVERTENCIA_ALTA"
    elif temp < TEMP_NORMAL_MIN:
        return "ADVERTENCIA_BAJA"
    return "NORMAL"

def _clasificar_hum(hum):
    if hum < HUM_NORMAL_MIN:
        return "HUMEDAD_BAJA"
    elif hum > HUM_NORMAL_MAX:
        return "HUMEDAD_ALTA"
    return "NORMAL"


def _leer_y_programar():
   
    global _ultima_temp, _ultima_hum, _estado_temp, _estado_hum, _timer_lectura

    try:
        temp = sensor_dht.temperature
        hum  = sensor_dht.humidity

        if temp is None or hum is None or temp <= 1.0:
            raise RuntimeError("Lectura inválida")

        _ultima_temp  = temp
        _ultima_hum   = hum
        _estado_temp  = _clasificar_temp(temp)
        _estado_hum   = _clasificar_hum(hum)
        hora          = datetime.now().strftime("%H:%M:%S")

        lcd.actualizar_seccion("temp", f"{temp:.1f}C {_estado_temp}")
        lcd.actualizar_seccion("hum",  f"{hum:.0f}% {_estado_hum}")

        if _estado_temp == "ADVERTENCIA_ALTA":
            print(f"[DHT11] Temp alta ({temp}°C) → activando ventilador")
            _cb_temp_alta(segundos=20, origen="AUTO_TEMP")
            lcd.mostrar_alerta_fija("TEMP ALTA", f"{temp:.1f}C VENTILANDO")

        # Publicar temperatura
        _publicar(TOPIC_DHT_TEMP, {
            "sensor": "temperatura",
            "valor":  temp,
            "estado": _estado_temp,
            "hora":   hora
        })
        _registrar("temperatura", temp, _estado_temp)

        # Publicar humedad
        _publicar(TOPIC_DHT_HUM, {
            "sensor": "humedad_ambiente",
            "valor":  hum,
            "estado": _estado_hum,
            "hora":   hora
        })
        _registrar("humedad_ambiente", hum, _estado_hum)

        # Estado global del invernadero
        if _estado_temp != "NORMAL" or _estado_hum != "NORMAL":
            estado_global = "ADVERTENCIA"
            _publicar(TOPIC_ESTADO_GLOBAL, {
                "estado":      "ADVERTENCIA",
                "causa_temp":  _estado_temp,
                "causa_hum":   _estado_hum,
                "hora":        hora
            })
            _db["eventos"].insert_one({
                "tipo":   "ADVERTENCIA_AMBIENTAL",
                "temp":   temp,
                "hum":    hum,
                "estado_temp": _estado_temp,
                "estado_hum":  _estado_hum,
                "fecha":  datetime.now()
            }) if _db else None
        else:
            estado_global = "NORMAL"

        # Activar ventilador si temperatura alta
        if _estado_temp == "ADVERTENCIA_ALTA" and _cb_temp_alta:
            print(f"[DHT11] Temp alta ({temp}°C) → activando ventilador")
            _cb_temp_alta(segundos=20, origen="AUTO_TEMP")

        print(f"[DHT11] {temp:.1f}°C ({_estado_temp}) | {hum:.1f}% ({_estado_hum}) | global: {estado_global}")

    except (RuntimeError, OverflowError):
        print("[DHT11] Lectura fallida, reintentando...")

    except Exception as e:
        print(f"[DHT11] Error inesperado: {e}")

    finally:
        intervalo = max(INTERVALO_LECTURA_SEG, 2)
        _timer_lectura = threading.Timer(intervalo, _leer_y_programar)
        _timer_lectura.daemon = True
        _timer_lectura.start()

def iniciar():
    print("[DHT11] Iniciando lecturas periódicas...")
    _leer_y_programar()   # primera lectura inmediata, luego se autoprograma

def detener():
    global _timer_lectura
    if _timer_lectura:
        _timer_lectura.cancel()
        _timer_lectura = None
    try:
        sensor_dht.exit()
    except Exception:
        pass
    print("[DHT11] Detenido.")

def get_ultima_lectura():
    return {
        "temperatura":  _ultima_temp,
        "estado_temp":  _estado_temp,
        "humedad_ambiente": _ultima_hum,
        "estado_hum":   _estado_hum
    }
