import os
import sys
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from gpiozero import Button # Librería moderna para evitar el error de edge detection

# Parche de ruta automática para encontrar config.py desde la carpeta raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    BROKER, PORT, CLIENT_ID_ACTUADOR, PIN_BOMBA, PIN_BOTON_RIEGO,
    DURACION_RIEGO, PAUSA_MINIMA, RELE_ACTIVO_EN_LOW,
    TOPIC_SUELO_AREA1, TOPIC_PUB_GLOBAL
)

def rele(encender):
    if RELE_ACTIVO_EN_LOW:
        return GPIO.LOW if encender else GPIO.HIGH
    return GPIO.HIGH if encender else GPIO.LOW

# Inicialización obligatoria de MongoDB para evitar caídas en publicar_estado
from pymongo import MongoClient
# Se asume conexión local por defecto a MongoDB. Ajusta si tu config tiene otra ruta.
cliente_mongo = MongoClient("mongodb://localhost:27000/") 
db = cliente_mongo['arqui1_db'] 

# Tópicos específicos para el control del riego local
TOPIC_MODO_RIEGO    = "Arqui1_G8_P1/actuadores/riego/modo"     # AUTOMATICO / MANUAL
TOPIC_CONTROL_RIEGO = "Arqui1_G8_P1/actuadores/riego/control"  # ENCENDER / APAGAR

# Configuración física de los Pines GPIO para la Bomba
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_BOMBA, GPIO.OUT, initial=rele(False))

# Configuración del Botón Físico con Gpiozero (Soluciona el error de hardware)
# bounce_time=0.5 equivale a bouncetime=500 de RPi.GPIO para filtrar chispas
boton_riego = Button(PIN_BOTON_RIEGO, bounce_time=0.5)

# Variables de Control de Estado de Seguridad (Relojes sin bloqueo)
modo_actual = "AUTOMATICO"     # Modos: AUTOMATICO / MANUAL
estado_riego = "RIEGO_OFF"     # Estados: RIEGO_OFF, RIEGO_AREA_1, RIEGO_MANUAL, BLOQUEADO_POR_SATURACION
ultimo_riego_timestamp = 0     # Guarda el tiempo de la última activación
suelo_esta_saturado = False    # Bandera de protección crítica de inundación

def publicar_estado(nuevo_estado, detalle_texto):
    global estado_riego
    estado_riego = nuevo_estado
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Registro en MongoDB (Pág 16: actuator_logs)
    db['actuator_logs'].insert_one({
        "actuador": "Bomba",
        "estado": nuevo_estado,
        "detalle": detalle_texto,
        "fecha": datetime.now()
    })
    
    print(f"[REGISTRO] {nuevo_estado}: {detalle_texto}")
    cliente.publish(TOPIC_PUB_GLOBAL, f"Estado: {nuevo_estado} | {detalle_texto}", qos=1)
    
def ejecutar_ciclo_riego(origen_comando):
    """Enciende la bomba controlando estrictamente el tiempo y aplicando las reglas de protección."""
    global ultimo_riego_timestamp
    ahora = time.time()

    # REGLA OBLIGATORIA: Impedir el riego si el suelo está saturado
    if suelo_esta_saturado:
        publicar_estado("BLOQUEADO_POR_SATURACION", "Intento de riego rechazado: El suelo ya tiene demasiada agua.")
        return

    # REGLA OBLIGATORIA: Pausa mínima de seguridad entre ciclos de riego
    tiempo_transcurrido = ahora - ultimo_riego_timestamp
    if tiempo_transcurrido < PAUSA_MINIMA:
        segundos_restantes = int(PAUSA_MINIMA - tiempo_transcurrido)
        print(f"[ALERTA] Bloqueo de seguridad: Espera {segundos_restantes}s para volver a regar.")
        return

    # Determinar el estado visual según quién activó el sistema
    estado_visual = "RIEGO_MANUAL" if origen_comando in ["BOTON_FISICO", "DASHBOARD_MANUAL"] else "RIEGO_AREA_1"

    # --- INICIO DEL RIEGO ---
    GPIO.output(PIN_BOMBA, rele(True))
    publicar_estado(estado_visual, f"Bomba encendida por {DURACION_RIEGO}s desde {origen_comando}.")

    # REGLA OBLIGATORIA: La bomba no se queda encendida indefinidamente (Duración controlada)
    time.sleep(DURACION_RIEGO)

    # --- FIN DEL RIEGO ---
    GPIO.output(PIN_BOMBA, rele(False))
    ultimo_riego_timestamp = time.time()  # Guarda el momento exacto en el que terminó
    
    publicar_estado("RIEGO_OFF", f"Bomba apagada de forma segura tras cumplir ciclo de {DURACION_RIEGO}s.")

def al_presionar_boton_fisico():
    """Interrupción de hardware manejada por Gpiozero de forma asíncrona."""
    print("[SISTEMA] Botón físico de riego presionado.")
    ejecutar_ciclo_riego("BOTON_FISICO")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[RIEGO] Conectado a EMQX con éxito. Monitoreando automatismos...")
        # Nos suscribimos a los canales para escuchar al sensor de suelo y las órdenes del usuario
        client.subscribe(TOPIC_SUELO_AREA1)
        client.subscribe(TOPIC_MODO_RIEGO)
        client.subscribe(TOPIC_CONTROL_RIEGO)
    else:
        print(f"[RIEGO] Error de conexión: {rc}")

def on_message(client, userdata, msg):
    global modo_actual, suelo_esta_saturado
    try:
        contenido = msg.payload.decode().strip()

        # 1. Escuchar la humedad del suelo enviada por main.py (Controlador Automático)
        if msg.topic == TOPIC_SUELO_AREA1:
            # Monitoreamos si la tierra se saturó de agua
            if "Estado: SATURADO" in contenido:
                suelo_esta_saturado = True
            else:
                suelo_esta_saturado = False

            # Si el modo es AUTOMATICO y detectamos suelo SECO, regamos solo si pasa el filtro
            if modo_actual == "AUTOMATICO" and "Estado: SECO" in contenido:
                ejecutar_ciclo_riego("AUTOMATICO_SENSOR")

        # 2. Escuchar cambios de Modo (AUTOMATICO / MANUAL) desde el Dashboard
        elif msg.topic == TOPIC_MODO_RIEGO:
            if contenido in ["AUTOMATICO", "MANUAL"]:
                modo_actual = contenido
                print(f"[SISTEMA] Modo de riego cambiado a: {modo_actual}")

        # 3. Escuchar órdenes de Riego Remoto (Solo permitidas en modo MANUAL)
        elif msg.topic == TOPIC_CONTROL_RIEGO:
            if contenido == "REGAR":
                if modo_actual == "MANUAL":
                    ejecutar_ciclo_riego("DASHBOARD_MANUAL")
                else:
                    print("[SISTEMA] Comando 'REGAR' ignorado. El sistema se encuentra en modo AUTOMATICO.")

    except Exception as e:
        print(f"[RIEGO] Error procesando mensaje de red: {e}")

# Configurar el cliente MQTT del Riego
cliente = mqtt.Client(client_id=CLIENT_ID_ACTUADOR, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
cliente.on_connect = on_connect
cliente.on_message = on_message
cliente.connect(BROKER, PORT, 60)
cliente.loop_start()

# Vinculamos la interrupción asíncrona del botón usando Gpiozero de forma segura
boton_riego.when_pressed = al_presionar_boton_fisico

print("Controlador de Riego de 1 Área Desplegado. Esperando eventos...")

try:
    while True:
        # El hilo principal descansa sin congelar los eventos de red ni el botón físico
        time.sleep(1)
except KeyboardInterrupt:
    print("\nDeteniendo controlador de riego.")
finally:
    GPIO.output(PIN_BOMBA, rele(False))
    GPIO.cleanup([PIN_BOMBA]) # Limpiamos solo la bomba, el botón se cierra automáticamente mediante Gpiozero
    boton_riego.close() # Cierre limpio del hardware del botón
    cliente.loop_stop()
    cliente.disconnect()
