import paho.mqtt.client as mqtt

BROKER = "broker.emqx.io"
PORT = 1883

TOPIC = "invernadero/G8/P1/sensores/temperatura"

cliente = mqtt.Client()

print("Conectando...")

cliente.connect(
    BROKER,
    PORT,
    60
)

cliente.loop_start()

cliente.publish(
    TOPIC,
    "25",
    qos=0
)

print("Mensaje enviado")

cliente.loop_stop()

cliente.disconnect()