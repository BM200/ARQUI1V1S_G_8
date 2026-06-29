"""
lcd.py — Controlador de pantalla LCD 16x2 vía I2C
Grupo 8 / Proyecto 1

Escucha tópicos MQTT de riego y luces y actualiza la LCD en tiempo real.

NOTA: Este archivo no requería cambios de lógica.
Se mantiene igual al original; solo se agrega documentación.

Dirección I2C: 0x27 (estándar PCF8574).
Si la pantalla no responde, ejecutá:
    i2cdetect -y 1
y cambiá 0x27 por la dirección que aparezca (frecuentemente 0x3F).
"""

import os
import sys
import time
import paho.mqtt.client as mqtt
from RPLCD.i2c import CharLCD

# Parche automático de ruta para encontrar config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    BROKER, PORT, TOPIC_PUB_GLOBAL, TOPIC_ESTADO_LUZ_AREA1, TOPIC_LDR
)

# Inicializar la pantalla LCD mediante I2C
lcd = CharLCD('PCF8574', 0x27, port=1, cols=16, rows=2)

# Estado actual mostrado en pantalla (evita refrescos redundantes)
ultimo_estado_riego = "RIEGO_OFF"
ultimo_estado_luces = "APAGADAS"


def actualizar_pantalla_fisica():
    """Limpia la LCD y escribe los estados actuales de forma fija y ordenada."""
    lcd.clear()

    # Fila 1: Estado del Riego
    lcd.cursor_pos = (0, 0)
    lcd.write_string(f"Rgo:{ultimo_estado_riego}")

    # Fila 2: Estado de las Luces
    lcd.cursor_pos = (1, 0)
    lcd.write_string(f"Luz:{ultimo_estado_luces}")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[LCD] Conectado a EMQX. Esperando eventos para mostrar en pantalla...")
        client.subscribe(TOPIC_PUB_GLOBAL)
        client.subscribe(TOPIC_ESTADO_LUZ_AREA1)
        client.subscribe(TOPIC_LDR)

        # Mensaje de bienvenida inicial
        lcd.clear()
        lcd.write_string("SISTEMA INVERNAD.")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("G8 - DESPLEGADO")
    else:
        print(f"[LCD] Error de conexión: {rc}")


def on_message(client, userdata, msg):
    global ultimo_estado_riego, ultimo_estado_luces
    try:
        contenido = msg.payload.decode().strip()

        # 1. Estado del Riego
        if msg.topic == TOPIC_PUB_GLOBAL:
            if "Estado: RIEGO_AREA_1" in contenido:
                ultimo_estado_riego = "RIEGO_A1"
            elif "Estado: RIEGO_MANUAL" in contenido:
                ultimo_estado_riego = "MANUAL"
            elif "Estado: BLOQUEADO_POR_SATURACION" in contenido:
                ultimo_estado_riego = "BLOQ_SAT"
            elif "Estado: RIEGO_OFF" in contenido or contenido == "OFF":
                ultimo_estado_riego = "OFF"
            elif contenido == "ON":
                ultimo_estado_riego = "ACTIVO"
            actualizar_pantalla_fisica()

        # 2. Estado de las Luces
        elif msg.topic == TOPIC_ESTADO_LUZ_AREA1 or msg.topic == TOPIC_LDR:
            if "ENCENDIDAS" in contenido or "Estado: OSCURO" in contenido:
                ultimo_estado_luces = "ENC_BAJA"
            elif "APAGADAS" in contenido or "Estado: ADECUADO" in contenido or "SUFICIENTE" in contenido:
                ultimo_estado_luces = "APAG_OK"
            actualizar_pantalla_fisica()

    except Exception as e:
        print(f"[LCD] Error actualizando texto: {e}")


# Configurar el cliente MQTT para la pantalla
cliente = mqtt.Client(
    client_id="actuador_lcd_G8",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
cliente.on_connect = on_connect
cliente.on_message = on_message
cliente.connect(BROKER, PORT, 60)

try:
    cliente.loop_forever()
except KeyboardInterrupt:
    print("\nApagando controlador de pantalla LCD.")
finally:
    lcd.clear()
    lcd.write_string("SISTEMA APAGADO")
    cliente.disconnect()
