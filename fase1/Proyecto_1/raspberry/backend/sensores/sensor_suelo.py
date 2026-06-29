from datetime import datetime
from config import UMBRAL_NORMAL, UMBRAL_SATURADO, UMBRAL_SECO, TOPIC_SUELO_AREA1, TOPIC_SUELO_AREA2

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
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = f"Estado: {estado} | Valor: {valor_crudo} | Fecha: {fecha}"
        topic = TOPIC_SUELO_AREA1 if area == 1 else TOPIC_SUELO_AREA2
        return topic, payload, estado
    except Exception as e:
        print(f"[ERROR SUELO] {e}")
        return TOPIC_SUELO_AREA1, "Error", "NORMAL"