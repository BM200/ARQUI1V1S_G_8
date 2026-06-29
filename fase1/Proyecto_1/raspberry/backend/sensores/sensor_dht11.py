import time
import adafruit_dht
import board
from config import UMBRAL_TEMP_ALTA
#import adafruit_dht
#import board

sensor = adafruit_dht.DHT11(board.D4, use_pulseio=False)

def leer_ambiente(reintentos: int = 3, pausa: float = 1.0):
    sensor = adafruit_dht.DHT11(board.D4)

    for intento in range(reintentos):
        try:
            temperatura = sensor.temperature
            humedad     = sensor.humidity

            if temperatura is not None and humedad is not None:
                estado = "ADVERTENCIA" if temperatura > UMBRAL_TEMP_ALTA else "NORMAL"
                sensor.exit()
                return temperatura, humedad, estado

        except RuntimeError as e:
            # El DHT11 lanza RuntimeError en lecturas fallidas — es esperado
            print(f"[DHT11] Intento {intento + 1}/{reintentos} fallido: {e}")
            time.sleep(pausa)

        except Exception as e:
            print(f"[DHT11] Error inesperado: {e}")
            break

    sensor.exit()
    return None, None, "ERROR"
