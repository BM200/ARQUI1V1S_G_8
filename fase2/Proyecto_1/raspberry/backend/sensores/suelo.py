import json
from datetime import datetime
from config import (
    UMBRAL_NORMAL, UMBRAL_SATURADO, UMBRAL_SECO,
    TOPIC_SUELO_AREA1, TOPIC_SUELO_AREA2
)
from sensores import lcd  

_db           = None
_cliente_mqtt = None  

def set_db(db):
    global _db
    _db = db

def set_cliente_mqtt(cliente):  
    global _cliente_mqtt
    _cliente_mqtt = cliente

def clasificar_humedad(valor):
    if valor >= UMBRAL_SECO:
        return "SECO"
    elif valor <= UMBRAL_SATURADO:
        return "SATURADO"
    else:
        return "NORMAL"

def procesar(valor_crudo, area):
    try:
        estado = clasificar_humedad(valor_crudo)
        fecha  = datetime.now()
        topic  = TOPIC_SUELO_AREA1 if area == 1 else TOPIC_SUELO_AREA2

        payload = json.dumps({
            "sensor": f"suelo_area{area}",
            "valor":  valor_crudo,
            "estado": estado,
            "hora":   fecha.strftime("%H:%M:%S")
        })

        # MQTT
        if _cliente_mqtt:
            _cliente_mqtt.publish(topic, payload, qos=1)

        # MongoDB
        if _db is not None:
            try:
                _db["sensor_logs"].insert_one({
                    "sensor": f"suelo_area{area}",
                    "valor":  valor_crudo,
                    "estado": estado,
                    "fecha":  fecha
                })
            except Exception:
                pass

        if estado == "SECO":
            lcd.mostrar_alerta_fija(f"SUELO A{area} SECO", "REGANDO...")
        else:
            lcd.actualizar_seccion(f"suelo{area}", f"{valor_crudo} {estado}")

        return topic, payload, estado

    except Exception as e:
        print(f"[ERROR SUELO] {e}")
        topic = TOPIC_SUELO_AREA1 if area == 1 else TOPIC_SUELO_AREA2
        return topic, "{}", "NORMAL"