from datetime import datetime
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BROKER, PORT,
    PIN_LEDS_BLANCOS_1, PIN_LEDS_BLANCOS_2, RELE_ACTIVO_EN_LOW,
    TOPIC_LDR, TOPIC_MODO_LUZ, TOPIC_CONTROL_LUZ,
    TOPIC_ESTADO_LUZ_AREA1, TOPIC_ESTADO_LUZ_AREA2
)

def rele(encender):
    if RELE_ACTIVO_EN_LOW:
        return GPIO.LOW if encender else GPIO.HIGH
    return GPIO.HIGH if encender else GPIO.LOW


# ==========================================================
# CONFIGURACIÓN GPIO
# ==========================================================

GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_LEDS_BLANCOS_1, GPIO.OUT, initial=rele(False))
GPIO.setup(PIN_LEDS_BLANCOS_2, GPIO.OUT, initial=rele(False))


# ==========================================================
# VARIABLES DE CONTROL
# ==========================================================

modo_actual = "AUTOMATICO"
estado_luces = "APAGADAS"


# ==========================================================
# FUNCIÓN PARA ACTUALIZAR LUCES
# ==========================================================
def actualizar_luces(nuevo_estado, origen):
    """
    Enciende o apaga los LEDs de ambas áreas.
    nuevo_estado: ENCENDIDAS / APAGADAS
    origen: AUTO / MANUAL
    """

    global estado_luces

    if estado_luces == nuevo_estado:
        return

    estado_luces = nuevo_estado
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nuevo_estado == "ENCENDIDAS":
        GPIO.output(PIN_LEDS_BLANCOS_1, rele(True))
        GPIO.output(PIN_LEDS_BLANCOS_2, rele(True))

        if origen == "AUTO":
            payload = f"Luces ENCENDIDAS automáticamente por baja luz ({fecha})"
        else:
            payload = f"Luces ENCENDIDAS manualmente por usuario ({fecha})"

    elif nuevo_estado == "APAGADAS":
        GPIO.output(PIN_LEDS_BLANCOS_1, rele(False))
        GPIO.output(PIN_LEDS_BLANCOS_2, rele(False))

        if origen == "AUTO":
            payload = f"Luces APAGADAS automáticamente por luz suficiente ({fecha})"
        else:
            payload = f"Luces APAGADAS manualmente por usuario ({fecha})"

    else:
        print(f"[LUCES] Estado no reconocido: {nuevo_estado}")
        return

    
    print(f"[REGISTRO EVENTO LUCES] {payload}")

    cliente.publish(
        TOPIC_ESTADO_LUZ_AREA1,
        f"Área 1: {nuevo_estado} | Modificado por {origen}",
        qos=1,
        retain=False
    )

    cliente.publish(
        TOPIC_ESTADO_LUZ_AREA2,
        f"Área 2: {nuevo_estado} | Modificado por {origen}",
        qos=1,
        retain=False
    )


# ==========================================================
# CALLBACK MQTT: CONEXIÓN
# ==========================================================

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[LUCES] Conectado correctamente al broker MQTT.")
        print("[LUCES] Sistema iniciado en modo AUTOMATICO.")
        print("[LUCES] LEDs iniciados APAGADOS.")

        client.subscribe(TOPIC_LDR)
        client.subscribe(TOPIC_MODO_LUZ)
        client.subscribe(TOPIC_CONTROL_LUZ)

        print(f"[LUCES] Suscrito a: {TOPIC_LDR}")
        print(f"[LUCES] Suscrito a: {TOPIC_MODO_LUZ}")
        print(f"[LUCES] Suscrito a: {TOPIC_CONTROL_LUZ}")

    else:
        print(f"[LUCES] Error de conexión MQTT. Código: {rc}")


# ==========================================================
# CALLBACK MQTT: MENSAJES RECIBIDOS
# ==========================================================

def on_message(client, userdata, msg):
    global modo_actual

    try:
        contenido = msg.payload.decode().strip()

        print(
            f"[MQTT RECIBIDO] Topic: {msg.topic} | "
            f"Mensaje: {contenido} | Retain: {msg.retain}"
        )

        # Evita actuar con mensajes retenidos antiguos del broker
        if msg.retain:
            print("[SISTEMA] Mensaje retenido ignorado.")
            return

        # ===============================
        # CAMBIO DE MODO
        # ===============================
        if msg.topic == TOPIC_MODO_LUZ:
            if contenido in ["AUTOMATICO", "MANUAL"]:
                modo_actual = contenido
                print(f"[SISTEMA] Modo de iluminación cambiado a: {modo_actual}")
            else:
                print(f"[SISTEMA] Modo no reconocido: {contenido}")

        # ===============================
        # CONTROL MANUAL
        # ===============================
        elif msg.topic == TOPIC_CONTROL_LUZ:
            if modo_actual == "MANUAL":
                if contenido == "ENCENDER":
                    actualizar_luces("ENCENDIDAS", "MANUAL")

                elif contenido == "APAGAR":
                    actualizar_luces("APAGADAS", "MANUAL")

                else:
                    print(f"[SISTEMA] Comando manual no reconocido: {contenido}")

            else:
                print("[SISTEMA] Comando manual ignorado. El sistema está en AUTOMATICO.")

        # ===============================
        # CONTROL AUTOMÁTICO POR LDR
        # ===============================
        elif msg.topic == TOPIC_LDR:
            if modo_actual == "AUTOMATICO":

                if "OSCURO" in contenido:
                    actualizar_luces("ENCENDIDAS", "AUTO")

                elif "ADECUADO" in contenido or "SUFICIENTE" in contenido:
                    actualizar_luces("APAGADAS", "AUTO")

                elif "Estado: EXCESIVO" in contenido:
                    actualizar_luces("APAGADAS", "AUTO")

                else:
                    print(f"[SISTEMA] Estado de luz no reconocido: {contenido}")

            else:
                print("[SISTEMA] Lectura LDR recibida, pero el sistema está en MANUAL.")

    except Exception as e:
        print(f"[LUCES] Error procesando mensaje: {e}")

# ==========================================================
# INICIO DEL CLIENTE MQTT
# ==========================================================

cliente = mqtt.Client(
    client_id="actuador_luz_G8",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

cliente.on_connect = on_connect
cliente.on_message = on_message

cliente.connect(BROKER, PORT, 60)


try:
    cliente.loop_forever()

except KeyboardInterrupt:
    print("\nApagando controlador de iluminación.")

finally:
    GPIO.output(PIN_LEDS_BLANCOS_1, rele(False))
    GPIO.output(PIN_LEDS_BLANCOS_2, rele(False))
    GPIO.cleanup()
    cliente.disconnect()
