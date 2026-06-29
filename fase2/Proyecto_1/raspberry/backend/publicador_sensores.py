"""Publicador de sensores físicos desde Arduino hacia MQTT."""
import random
import time
from typing import List, Optional

import paho.mqtt.client as mqtt

from config import (
    BROKER,
    CLIENT_ID_PUBLICADOR,
    IDX_GAS,
    IDX_LDR,
    IDX_SUELO1,
    IDX_SUELO2,
    INTERVALO_LECTURA_SEG,
    KEEPALIVE,
    NUM_VALORES,
    PORT,
    PUERTO_SERIAL,
    VELOCIDAD,
)
from sensores import sensor_gas, sensor_luz, sensor_suelo

try:
    import serial
except ImportError:
    serial = None


def on_connect(client, userdata, flags, reason_code, properties=None):
    if int(reason_code) == 0:
        print("[PUBLICADOR] Conectado al broker MQTT.")
    else:
        print(f"[PUBLICADOR] Error de conexión MQTT: {reason_code}")


def leer_linea_reciente(arduino) -> Optional[str]:
    try:
        arduino.reset_input_buffer()
        time.sleep(0.05)
        linea = arduino.readline()
        if not linea:
            return None
        return linea.decode("utf-8", errors="ignore").strip()
    except Exception as exc:
        print(f"[SERIAL] Error leyendo Arduino: {exc}")
        return None


def parsear_valores(linea: str) -> Optional[List[int]]:
    try:
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != NUM_VALORES:
            print(f"[SERIAL] Línea inválida: {linea}")
            return None
        return [int(parte) for parte in partes]
    except ValueError:
        print(f"[SERIAL] No se pudo convertir a números: {linea}")
        return None


def publicar_valores(cliente, valores: List[int]):
    t_gas, p_gas, e_gas = sensor_gas.procesar(valores[IDX_GAS])
    t1, p1, e1 = sensor_suelo.procesar(valores[IDX_SUELO1], area=1)
    t2, p2, e2 = sensor_suelo.procesar(valores[IDX_SUELO2], area=2)
    t_luz, p_luz, e_luz = sensor_luz.procesar(valores[IDX_LDR])

    for topic, payload in [(t_gas, p_gas), (t1, p1), (t2, p2), (t_luz, p_luz)]:
        cliente.publish(topic, payload, qos=1, retain=False)

    print(f"[SENSORES] Gas={e_gas}({valores[IDX_GAS]}) | S1={e1}({valores[IDX_SUELO1]}) | S2={e2}({valores[IDX_SUELO2]}) | Luz={e_luz}({valores[IDX_LDR]})")


def valores_simulados() -> List[int]:
    gas = random.randint(90, 130)
    suelo1 = random.randint(250, 850)
    suelo2 = random.randint(250, 850)
    luz = random.randint(20, 950)
    return [gas, suelo1, suelo2, luz]


def main(stop_event=None, sim: bool = False):
    cliente = mqtt.Client(client_id=CLIENT_ID_PUBLICADOR, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = on_connect

    arduino = None
    try:
        cliente.connect(BROKER, PORT, KEEPALIVE)
        cliente.loop_start()

        if not sim:
            if serial is None:
                print("[SERIAL] pyserial no instalado. Cambiando a modo simulación.")
                sim = True
            else:
                arduino = serial.Serial(PUERTO_SERIAL, VELOCIDAD, timeout=5)
                time.sleep(2)
                print(f"[SERIAL] Arduino conectado en {PUERTO_SERIAL}")

        print("[PUBLICADOR] Publicando sensores...")
        ultimo_tiempo = 0.0

        while stop_event is None or not stop_event.is_set():
            ahora = time.time()
            if ahora - ultimo_tiempo < INTERVALO_LECTURA_SEG:
                time.sleep(0.05)
                continue

            if sim:
                valores = valores_simulados()
            else:
                linea = leer_linea_reciente(arduino)
                if not linea:
                    continue
                valores = parsear_valores(linea)
                if valores is None:
                    continue

            publicar_valores(cliente, valores)
            ultimo_tiempo = ahora

    except Exception as exc:
        print(f"[PUBLICADOR] Error: {exc}")
    finally:
        if arduino is not None:
            arduino.close()
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()
