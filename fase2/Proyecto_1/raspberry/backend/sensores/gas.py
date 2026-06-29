import json
import threading
from datetime import datetime
from gpiozero import LED, Buzzer, OutputDevice
from sensores import lcd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    TOPIC_GAS, TOPIC_ESTADO_GLOBAL, TOPIC_ALARMA, TOPIC_VENTILADOR,
    UMBRAL_GAS_NORMAL, UMBRAL_GAS_ALERTA,
    LED_VERDE, LED_AMARILLO, LED_ROJO,
    PIN_ALARMA, PIN_VENTILADOR
)


led_verde    = LED(LED_VERDE)     # GPIO 5  — estado normal
led_amarillo = LED(LED_AMARILLO)  # GPIO 6  — advertencia
led_rojo     = LED(LED_ROJO)      # GPIO 13 — emergencia
#buzzer       = Buzzer(PIN_ALARMA,     active_high=False, initial_value=False)
buzzer       = Buzzer(PIN_ALARMA,     active_high=True, initial_value=False)
ventilador   = OutputDevice(PIN_VENTILADOR, active_high=False, initial_value=False)

# --- Estado interno ---
_estado_actual   = "GAS_NORMAL"
_en_emergencia   = False
_ultimo_valor    = 0

_db           = None
_cliente_mqtt = None

def set_db(db):
    global _db
    _db = db

def set_cliente_mqtt(cliente):
    global _cliente_mqtt
    _cliente_mqtt = cliente


def _publicar(topic, payload: dict):
    if _cliente_mqtt:
        _cliente_mqtt.publish(topic, json.dumps(payload), qos=1)

def _registrar(estado, valor, detalle=""):
    if _db is None:
        return
    _db["eventos"].insert_one({
        "tipo":    "GAS",
        "estado":  estado,
        "valor":   valor,
        "detalle": detalle,
        "fecha":   datetime.now()
    })

def _apagar_leds():
    led_verde.off()
    led_amarillo.off()
    led_rojo.off()


def procesar(valor_gas: int):

    global _estado_actual, _en_emergencia, _ultimo_valor
    _ultimo_valor = valor_gas
    hora = datetime.now().strftime("%H:%M:%S")

    if _en_emergencia:
        if valor_gas > UMBRAL_GAS_ALERTA:
            # sigue en emergencia — mantener actuadores activos
            led_rojo.on()
            buzzer.on()
            ventilador.on()
        # aunque baje, seguimos en emergencia hasta reset manual
        _publicar(TOPIC_GAS, {
            "sensor": "gas",
            "valor":  valor_gas,
            "estado": "GAS_EMERGENCIA",
            "bloqueado": True,   # le dice al dashboard que necesita reset
            "hora":   hora
        })
        return "GAS_EMERGENCIA"

    _apagar_leds()
    buzzer.off()
    ventilador.off()

    if valor_gas < UMBRAL_GAS_NORMAL:           # < 200
        _estado_actual = "GAS_NORMAL"
        led_verde.on()

    elif valor_gas <= UMBRAL_GAS_ALERTA:         # 200–400
        _estado_actual = "GAS_ADVERTENCIA"
        led_amarillo.on()
        ventilador.on()
        _registrar("GAS_ADVERTENCIA", valor_gas, "Nivel elevado detectado")
        _publicar(TOPIC_ESTADO_GLOBAL, {
            "estado": "ADVERTENCIA",
            "causa":  "gas_elevado",
            "valor":  valor_gas,
            "hora":   hora
        })

        lcd.actualizar_seccion("gas", f"{_ultimo_valor} NORMAL")

    else:                                        # > 400 — EMERGENCIA
        _estado_actual  = "GAS_EMERGENCIA"
        _en_emergencia  = True
        led_rojo.on()
        buzzer.on()
        ventilador.on()

        # Cambiar estado global a Emergenckia
        _publicar(TOPIC_ESTADO_GLOBAL, {
            "estado": "EMERGENCIA",
            "causa":  "gas_peligroso",
            "valor":  valor_gas,
            "hora":   hora
        })
        # Publicar alarma
        _publicar(TOPIC_ALARMA, {
            "estado": "EMERGENCIA",
            "valor":  valor_gas,
            "hora":   hora
        })

        lcd.mostrar_alerta_fija("!! GAS !!", f"VALOR: {valor_gas}")

        _registrar("GAS_EMERGENCIA", valor_gas, "EMERGENCIA — activación de buzzer y ventilador")
        print(f"[GAS] EMERGENCIA — valor: {valor_gas}. Reset manual requerido.")

    # Publicar lectura normal
    _publicar(TOPIC_GAS, {
        "sensor": "gas",
        "valor":  valor_gas,
        "estado": _estado_actual,
        "hora":   hora
    })

    print(f"[GAS] {valor_gas} → {_estado_actual}")
    return _estado_actual


def reset_emergencia():

    global _en_emergencia, _estado_actual

    if _ultimo_valor > UMBRAL_GAS_ALERTA:
        print("[GAS] Reset rechazado — el valor sigue en nivel peligroso.")
        _publicar(TOPIC_GAS, {
            "sensor":  "gas",
            "estado":  "RESET_RECHAZADO",
            "valor":   _ultimo_valor,
            "detalle": "El nivel de gas sigue siendo peligroso",
            "hora":    datetime.now().strftime("%H:%M:%S")
        })
        return False

    # Reset aprobado
    _en_emergencia = False
    _estado_actual = "GAS_NORMAL"
    _apagar_leds()
    buzzer.off()
    ventilador.off()
    led_verde.on()

    _registrar("RESET", _ultimo_valor, "Emergencia confirmada como resuelta por operador")
    _publicar(TOPIC_ESTADO_GLOBAL, {
        "estado": "NORMAL",
        "causa":  "reset_manual_gas",
        "hora":   datetime.now().strftime("%H:%M:%S")
    })

    lcd.actualizar_seccion("gas", f"{_ultimo_valor} NORMAL")
    lcd.reanudar_rotacion()
    print("[GAS] Emergencia reseteada. Sistema vuelve a NORMAL.")
    return True


def get_estado():
    return {
        "gas_valor":  _ultimo_valor,
        "gas_estado": _estado_actual,
        "emergencia": _en_emergencia
    }

def apagar_todo():
    _apagar_leds()
    buzzer.off()
    ventilador.off()