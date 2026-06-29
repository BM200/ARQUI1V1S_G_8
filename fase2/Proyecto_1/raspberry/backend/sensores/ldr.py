import json
from datetime import datetime
from gpiozero import LED

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    PIN_LEDS_BLANCOS_1, PIN_LEDS_BLANCOS_2,
    TOPIC_LDR, TOPIC_LUCES,
    UMBRAL_LUZ_BAJA
)
from sensores import lcd

led_area1 = LED(PIN_LEDS_BLANCOS_1)   # GPIO 12
led_area2 = LED(PIN_LEDS_BLANCOS_2)   # GPIO 26

_modo_luces   = "AUTOMATICO"
_db           = None
_cliente_mqtt = None
_luces_on   = False
_modo_luces = "AUTOMATICO"

def set_db(db):
    global _db
    _db = db

def set_cliente_mqtt(cliente):
    global _cliente_mqtt
    _cliente_mqtt = cliente

def set_modo_luces(modo):
    global _modo_luces
    _modo_luces = modo
    print(f"[LUCES] Modo: {modo}")

def encender_luces_manual():
    global _luces_on, _modo_luces
    _luces_on   = True
    _modo_luces = "MANUAL"
    led_area1.on()
    led_area2.on()
    print("[LUCES] ON — manual")
    _publicar_luces("MANUAL", "encendido_manual")
    lcd.actualizar_seccion("luz", "LUCES ON MANUAL")

def apagar_luces_manual():
    global _luces_on
    _luces_on = False
    led_area1.off()
    led_area2.off()
    print("[LUCES] OFF — manual")
    _publicar_luces("MANUAL", "apagado_manual")
    lcd.actualizar_seccion("luz", "LUCES OFF")

def _publicar_luces(modo, detalle):
    hora    = datetime.now().strftime("%H:%M:%S")
    payload = json.dumps({
        "sensor":  "luces",
        "modo":    modo,
        "detalle": detalle,
        "hora":    hora
    })
    if _cliente_mqtt:
        _cliente_mqtt.publish(TOPIC_LUCES, payload, qos=1)
    if _db is not None:
        _db["sensor_logs"].insert_one({
            "sensor":  "luces",
            "modo":    modo,
            "detalle": detalle,
            "fecha":   datetime.now()
        })

def procesar(valor_ldr: int):
    global _luces_on
    # Tu compañero usó: if luz_amb < 300 → encender
    estado = "OSCURO" if valor_ldr < UMBRAL_LUZ_BAJA else "LUZ"

    if _modo_luces == "AUTOMATICO":
        if estado == "OSCURO":
            led_area1.on()
            led_area2.on()
            _luces_on = True
        else:
            led_area1.off()
            led_area2.off()
            _luces_on = False
        _publicar_luces("AUTOMATICO", estado)

    if _cliente_mqtt:
        _cliente_mqtt.publish(TOPIC_LDR, json.dumps({
            "sensor": "luz",
            "valor":  valor_ldr,
            "estado": estado,
            "hora":   datetime.now().strftime("%H:%M:%S")
        }), qos=1)

    if _db is not None:
        try:
            _db["sensor_logs"].insert_one({
                "sensor": "luz",
                "valor":  valor_ldr,
                "estado": estado,
                "fecha":  datetime.now()
            })
        except Exception:
            pass

    lcd.actualizar_seccion("luz", f"{valor_ldr} {estado}")
    return estado
