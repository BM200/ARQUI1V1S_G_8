"""
Prueba fisica directa de actuadores del invernadero.

Ejecuta este archivo en la Raspberry con sudo y con main.py detenido.
Sirve para confirmar si el modulo rele/convertidor enciende con HIGH o LOW.
"""
import argparse
import time

import RPi.GPIO as GPIO

from config import (
    LED_AMARILLO,
    LED_ROJO,
    LED_VERDE,
    PIN_ALARMA,
    PIN_BOMBA_AREA1,
    PIN_LEDS_BLANCOS_1,
    PIN_LEDS_BLANCOS_2,
    PIN_VENTILADOR,
    RELE_ACTIVO_EN_LOW,
)


ACTUADORES = [
    ("bomba", PIN_BOMBA_AREA1),
    ("ventilador", PIN_VENTILADOR),
    ("buzzer", PIN_ALARMA),
    ("luz_area1", PIN_LEDS_BLANCOS_1),
    ("luz_area2", PIN_LEDS_BLANCOS_2),
]

LEDS_ESTADO = [
    ("led_verde", LED_VERDE),
    ("led_amarillo", LED_AMARILLO),
    ("led_rojo", LED_ROJO),
]


def niveles(modo):
    if modo == "config":
        activo_en_low = RELE_ACTIVO_EN_LOW
    else:
        activo_en_low = modo == "low"
    encendido = GPIO.LOW if activo_en_low else GPIO.HIGH
    apagado = GPIO.HIGH if activo_en_low else GPIO.LOW
    return encendido, apagado


def texto_nivel(nivel):
    return "HIGH" if nivel == GPIO.HIGH else "LOW"


def probar_salida(nombre, pin, encendido, apagado, segundos):
    print(f"[PRUEBA] {nombre} GPIO{pin} ON={texto_nivel(encendido)} por {segundos}s")
    GPIO.output(pin, encendido)
    time.sleep(segundos)
    GPIO.output(pin, apagado)
    print(f"[PRUEBA] {nombre} GPIO{pin} OFF={texto_nivel(apagado)}")
    time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modo",
        choices=["config", "high", "low"],
        default="config",
        help="config usa RELE_ACTIVO_EN_LOW; high fuerza ON=HIGH; low fuerza ON=LOW",
    )
    parser.add_argument("--segundos", type=float, default=2.0)
    args = parser.parse_args()

    encendido, apagado = niveles(args.modo)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([pin for _, pin in ACTUADORES], GPIO.OUT, initial=apagado)
    GPIO.setup([pin for _, pin in LEDS_ESTADO], GPIO.OUT, initial=GPIO.LOW)

    print("==========================================================")
    print(" Prueba directa de actuadores - detener main.py primero")
    print(f" Modo: {args.modo} | ON={texto_nivel(encendido)} OFF={texto_nivel(apagado)}")
    print("==========================================================")

    try:
        for nombre, pin in ACTUADORES:
            probar_salida(nombre, pin, encendido, apagado, args.segundos)

        for nombre, pin in LEDS_ESTADO:
            print(f"[PRUEBA] {nombre} GPIO{pin} ON=HIGH por {args.segundos}s")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(args.segundos)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.5)

    finally:
        GPIO.output([pin for _, pin in ACTUADORES], apagado)
        GPIO.output([pin for _, pin in LEDS_ESTADO], GPIO.LOW)
        GPIO.cleanup()
        print("[PRUEBA] Todas las salidas quedaron apagadas.")


if __name__ == "__main__":
    main()
