from datetime import datetime
from config import LDR_OSCURO_EN_VALOR_ALTO, UMBRAL_LUZ_BAJA, TOPIC_LDR

def clasificar_luz(valor):
    if LDR_OSCURO_EN_VALOR_ALTO and valor >= UMBRAL_LUZ_BAJA:
        return "OSCURO"
    if not LDR_OSCURO_EN_VALOR_ALTO and valor <= UMBRAL_LUZ_BAJA:
        return "OSCURO"
    return "SUFICIENTE"

def procesar(valor_crudo):
    try:
        estado = clasificar_luz(valor_crudo)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = f"Luz: {estado} | Valor: {valor_crudo} | Fecha: {fecha}"
        return TOPIC_LDR, payload, estado
    except Exception as e:
        print(f"[ERROR LUZ] {e}")
        return TOPIC_LDR, "Error", "SUFICIENTE"
