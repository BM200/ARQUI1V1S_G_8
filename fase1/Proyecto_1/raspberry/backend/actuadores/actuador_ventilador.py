import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from config import BROKER, PORT, PIN_VENTILADOR, RELE_ACTIVO_EN_LOW, TOPIC_VENTILADOR

CLIENT_ID_VENTILADOR = "actuador_ventilador_G8"

def rele(encender):
    if RELE_ACTIVO_EN_LOW:
        return GPIO.LOW if encender else GPIO.HIGH
    return GPIO.HIGH if encender else GPIO.LOW

def on_message(client, userdata, mensaje):
    payload = mensaje.payload.decode("utf-8").upper()
    print(f"[VENTILADOR] Acción recibida: {payload}")
    
    if payload == "ON":
        GPIO.output(PIN_VENTILADOR, rele(True))
        print("[HARDWARE] Ventilador encendido.")
    elif payload == "OFF":
        GPIO.output(PIN_VENTILADOR, rele(False))
        print("[HARDWARE] Ventilador apagado.")

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_VENTILADOR, GPIO.OUT)
    GPIO.output(PIN_VENTILADOR, rele(False))

    cliente = mqtt.Client(
        client_id=CLIENT_ID_VENTILADOR,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    cliente.on_message = on_message
    cliente.connect(BROKER, PORT, 60)
    
    cliente.subscribe(TOPIC_VENTILADOR)
    print("[VENTILADOR] Escuchando cambios de estado...")
    cliente.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[VENTILADOR] Deteniendo módulo.")
    finally:
        GPIO.cleanup(PIN_VENTILADOR)
