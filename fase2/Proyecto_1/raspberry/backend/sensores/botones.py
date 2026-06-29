import json
from datetime import datetime
from gpiozero import Button

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    PIN_BOTON_MODO, PIN_BOTON_RIEGO,
    PIN_BOTON_LUCES, PIN_BOTON_BUZZER_RESET,
    TOPIC_CONTROL_MANUAL, TOPIC_RIEGO_AREA1,
    TOPIC_LUCES, TOPIC_ALARMA
)

btn_modo  = Button(PIN_BOTON_MODO,         bounce_time=0.05)
btn_riego = Button(PIN_BOTON_RIEGO,        bounce_time=0.05)
btn_luces = Button(PIN_BOTON_LUCES,        bounce_time=0.05)
btn_reset = Button(PIN_BOTON_BUZZER_RESET, bounce_time=0.05)

_modo_actual      = "AUTOMATICO"
_luces_on         = False
_cliente_mqtt     = None
_activar_bomba_fn = None
_toggle_luces_fn  = None
_reset_gas_fn     = None

def set_cliente_mqtt(cliente):
    global _cliente_mqtt
    _cliente_mqtt = cliente

def _publicar(topic, payload: dict):
    if _cliente_mqtt:
        _cliente_mqtt.publish(topic, json.dumps(payload), qos=1)
    print(f"[BOTON] {topic} → {payload}")

def _parpadear():
    try:
        from sensores.gas import led_verde as _led
        _led.blink(on_time=0.1, off_time=0.1, n=3, background=True)
    except Exception:
        pass

def _btn1_modo():
    global _modo_actual
    _modo_actual = "MANUAL" if _modo_actual == "AUTOMATICO" else "AUTOMATICO"
    _parpadear()
    _publicar(TOPIC_CONTROL_MANUAL, {
        "modo":   _modo_actual,
        "origen": "BOTON_FISICO",
        "hora":   datetime.now().strftime("%H:%M:%S")
    })
    print(f"[BOTON] Modo cambiado a: {_modo_actual}")

def _btn2_riego():
    _parpadear()
    if _activar_bomba_fn:
        _activar_bomba_fn(origen="BOTON_FISICO")
    _publicar(TOPIC_RIEGO_AREA1, {
        "comando": "ENCENDER",
        "origen":  "BOTON_FISICO",
        "hora":    datetime.now().strftime("%H:%M:%S")
    })

def _btn3_luces():
    global _luces_on
    _luces_on = not _luces_on
    _parpadear()
    if _luces_on:
        from sensores.ldr import encender_luces_manual
        encender_luces_manual()
    else:
        from sensores.ldr import apagar_luces_manual
        apagar_luces_manual()
    _publicar(TOPIC_LUCES, {
        "comando": "ENCENDER" if _luces_on else "APAGAR",
        "origen":  "BOTON_FISICO",
        "hora":    datetime.now().strftime("%H:%M:%S")
    })

def _btn4_reset():
    print("[BOTON] BTN4 presionado — reset emergencia")  # ← siempre imprime
    _parpadear()
    try:
        from sensores.gas import buzzer as _buzzer
        _buzzer.off()   # ← apagar sin verificar .value
        print("[BOTON] Buzzer apagado")
    except Exception as e:
        print(f"[BOTON] Error buzzer: {e}")
    if _reset_gas_fn:
        _reset_gas_fn()
    _publicar(TOPIC_ALARMA, {
        "comando": "RESET",
        "origen":  "BOTON_FISICO",
        "hora":    datetime.now().strftime("%H:%M:%S")
    })
    print("[BOTON] Reset completado")

def configurar(activar_bomba_fn, activar_ventilador_fn,
               toggle_luces_fn, reset_gas_fn=None):
    global _activar_bomba_fn, _toggle_luces_fn, _reset_gas_fn

    _activar_bomba_fn = activar_bomba_fn
    _toggle_luces_fn  = toggle_luces_fn
    _reset_gas_fn     = reset_gas_fn

    btn_modo.when_pressed  = _btn1_modo
    btn_riego.when_pressed = _btn2_riego
    btn_luces.when_pressed = _btn3_luces
    btn_reset.when_pressed = _btn4_reset

    print(f"[BOTONES] 4 configurados: modo={PIN_BOTON_MODO}, "
          f"riego={PIN_BOTON_RIEGO}, luces={PIN_BOTON_LUCES}, "
          f"reset={PIN_BOTON_BUZZER_RESET}")
