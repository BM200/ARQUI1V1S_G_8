import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from config import (
    BROKER, PORT, PIN_BOTON_MODO, PIN_BOTON_RIEGO, 
    TOPIC_MODO_LUZ, TOPIC_PUB_1
)

CLIENT_ID_BOTONES = "puente_botones_G8"
MODO_ACTUAL_AUTO = True  # Bandera de estado local

def inicializar_botones():
    GPIO.setmode(GPIO.BCM)
    # Configuración con resistencia PULL_UP interna (el botón conecta a GND)
    GPIO.setup(PIN_BOTON_MODO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_BOTON_RIEGO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main():
    global MODO_ACTUAL_AUTO
    inicializar_botones()
    
    cliente = mqtt.Client(
        client_id=CLIENT_ID_BOTONES,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    cliente.connect(BROKER, PORT, 60)
    cliente.loop_start()
    
    print("[BOTONES] Monitoreando pulsadores físicos de la Pi...")
    
    try:
        while True:
            # 1. Monitoreo de Botón de Modo (Filtro antirrebote simple)
            if GPIO.input(PIN_BOTON_MODO) == GPIO.LOW:
                MODO_ACTUAL_AUTO = not MODO_ACTUAL_AUTO
                nuevo_modo = "AUTOMATICO" if MODO_ACTUAL_AUTO else "MANUAL"
                cliente.publish(TOPIC_MODO_LUZ, nuevo_modo, qos=1)
                print(f"[BOTÓN MODO] Cambiado localmente a: {nuevo_modo}")
                time.sleep(0.4) # Antirrebote (debounce)
                
            # 2. Monitoreo de Botón de Riego Manual
            if GPIO.input(PIN_BOTON_RIEGO) == GPIO.LOW:
                print("[BOTÓN RIEGO] Solicitud de riego manual enviada.")
                cliente.publish(TOPIC_PUB_1, "ON", qos=1)
                time.sleep(0.4) # Antirrebote (debounce)
                
            time.sleep(0.05) # Pequeña pausa para no saturar la CPU
            
    except KeyboardInterrupt:
        print("\n[BOTONES] Monitoreo finalizado.")
    finally:
        cliente.loop_stop()
        cliente.disconnect()
        GPIO.cleanup([PIN_BOTON_MODO, PIN_BOTON_RIEGO])

if __name__ == "__main__":
    main() 