from datetime import datetime
from config import UMBRAL_GAS_NORMAL, UMBRAL_GAS_ALERTA, TOPIC_GAS

def clasificar_gas(valor):
    """Clasifica según los estados obligatorios del PDF (Pág 12)."""
    if valor >= UMBRAL_GAS_ALERTA:
        return "GAS_EMERGENCIA"
    elif valor >= UMBRAL_GAS_NORMAL:
        return "GAS_ADVERTENCIA"
    else:
        return "GAS_NORMAL"

def procesar(valor_crudo):
    try:
        estado = clasificar_gas(valor_crudo)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = f"Calidad Aire: {estado} | Valor: {valor_crudo} | Fecha: {fecha}"
        return TOPIC_GAS, payload, estado
    except Exception as e:
        print(f"[ERROR GAS] {e}")
        return TOPIC_GAS, "Error", "GAS_NORMAL"