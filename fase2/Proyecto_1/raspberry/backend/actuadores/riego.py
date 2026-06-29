import threading
import time
import json
import RPi.GPIO as GPIO
from datetime import datetime

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    PIN_BOMBA, PIN_VENTILADOR,
    DURACION_RIEGO, PAUSA_MINIMA,
    TOPIC_RIEGO_AREA1, TOPIC_VENTILADOR, TOPIC_ESTADO_GLOBAL
)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_BOMBA,      GPIO.OUT, initial=GPIO.HIGH)  # HIGH = apagado
GPIO.setup(PIN_VENTILADOR, GPIO.OUT, initial=GPIO.HIGH)

def _encender(pin):
    GPIO.output(pin, GPIO.LOW)   # LOW activa el relé

def _apagar(pin):
    GPIO.output(pin, GPIO.HIGH)  # HIGH desactiva el relé


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
    print(f"[ACTUADOR] {topic} → {payload}")

def _registrar(actuador, estado, detalle):
    if _db is None:
        return
    _db["actuator_logs"].insert_one({
        "actuador": actuador,
        "estado":   estado,
        "detalle":  detalle,
        "fecha":    datetime.now()
    })


# Bomba
_ultimo_riego  = 0
_bomba_activa  = False
_timer_bomba   = None

def _apagar_bomba():

    global _bomba_activa, _ultimo_riego, _timer_bomba
    _apagar(PIN_BOMBA)
    _bomba_activa = False
    _ultimo_riego = time.time()
    _timer_bomba  = None
    _publicar(TOPIC_RIEGO_AREA1, {
        "estado":  "APAGADO",
        "detalle": f"Ciclo de {DURACION_RIEGO}s completado",
        "hora":    datetime.now().strftime("%H:%M:%S")
    })
    _registrar("bomba", "APAGADO", f"Ciclo de {DURACION_RIEGO}s completado")

def activar_bomba(origen="SISTEMA", segundos=None):

    global _bomba_activa, _timer_bomba
    duracion = segundos if segundos else DURACION_RIEGO

    if _bomba_activa:
        print("[BOMBA] Ya hay un ciclo activo.")
        return

    transcurrido = time.time() - _ultimo_riego
    if transcurrido < PAUSA_MINIMA:
        restante = int(PAUSA_MINIMA - transcurrido)
        print(f"[BOMBA] Pausa activa — quedan {restante}s")
        _publicar(TOPIC_ESTADO_GLOBAL, {
            "estado":  "BOMBA_BLOQUEADA",
            "detalle": f"Espera {restante}s",
            "hora":    datetime.now().strftime("%H:%M:%S")
        })
        return

    _bomba_activa = True
    _encender(PIN_BOMBA)

    _publicar(TOPIC_RIEGO_AREA1, {
        "estado":  "ENCENDIDO",
        "origen":  origen,
        "duracion": duracion,
        "hora":    datetime.now().strftime("%H:%M:%S")
    })
    _registrar("bomba", "ENCENDIDO", f"Activada por {origen} durante {duracion}s")

    # Timer — apaga sola al cumplir el tiempo, sin bloquear nada
    _timer_bomba = threading.Timer(duracion, _apagar_bomba)
    _timer_bomba.daemon = True
    _timer_bomba.start()

def cancelar_bomba():
    """Apagado inmediato — para emergencias o comando manual APAGAR."""
    global _bomba_activa, _timer_bomba
    if _timer_bomba:
        _timer_bomba.cancel()
        _timer_bomba = None
    _apagar(PIN_BOMBA)
    _bomba_activa = False
    _registrar("bomba", "CANCELADO", "Apagado manual")
    _publicar(TOPIC_RIEGO_AREA1, {
        "estado": "CANCELADO",
        "hora":   datetime.now().strftime("%H:%M:%S")
    })


# Ventilador

_vent_activo = False
_timer_vent  = None

def _apagar_ventilador():
    global _vent_activo, _timer_vent
    _apagar(PIN_VENTILADOR)
    _vent_activo = False
    _timer_vent  = None
    _publicar(TOPIC_VENTILADOR, {
        "estado": "APAGADO",
        "hora":   datetime.now().strftime("%H:%M:%S")
    })
    _registrar("ventilador", "APAGADO", "Ciclo completado")

def activar_ventilador(segundos=10, origen="SISTEMA"):
    global _vent_activo, _timer_vent
    if _vent_activo:
        print("[VENT] Ya está activo.")
        return

    _vent_activo = True
    _encender(PIN_VENTILADOR)

    _publicar(TOPIC_VENTILADOR, {
        "estado":  "ENCENDIDO",
        "origen":  origen,
        "duracion": segundos,
        "hora":    datetime.now().strftime("%H:%M:%S")
    })
    _registrar("ventilador", "ENCENDIDO", f"Activado {segundos}s por {origen}")

    _timer_vent = threading.Timer(segundos, _apagar_ventilador)
    _timer_vent.daemon = True
    _timer_vent.start()

def cancelar_ventilador():
    global _vent_activo, _timer_vent
    if _timer_vent:
        _timer_vent.cancel()
        _timer_vent = None
    _apagar(PIN_VENTILADOR)
    _vent_activo = False
    _registrar("ventilador", "CANCELADO", "Apagado manual")


# Apagado de emergencia total

def apagar_todo():
    cancelar_bomba()
    cancelar_ventilador()
    _publicar(TOPIC_ESTADO_GLOBAL, {
        "estado": "APAGADO_EMERGENCIA",
        "hora":   datetime.now().strftime("%H:%M:%S")
    })
    print("[ACTUADOR] Todo apagado.")

def limpiar_gpio():
    """Llamar solo al cerrar main.py — libera los pines."""
    _apagar(PIN_BOMBA)
    _apagar(PIN_VENTILADOR)
    GPIO.cleanup([PIN_BOMBA, PIN_VENTILADOR])