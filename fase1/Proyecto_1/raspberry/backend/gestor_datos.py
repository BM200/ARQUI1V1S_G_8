"""
gestor_datos.py
Recolecta datos de sensores desde MQTT, guarda exactamente 30 muestras en RAM,
crea un CSV temporal para los módulos ARM64 y expone los resultados al dashboard.
"""

from __future__ import annotations

import csv
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from config import (
    BROKER,
    PORT,
    TOPIC_GAS,
    TOPIC_SUELO_AREA1,
    TOPIC_SUELO_AREA2,
    TOPIC_LDR,
    TOPIC_DHT_TEMP,
    TOPIC_DHT_HUM,
)
from ejecutor_arm64 import ARM64_DIR, ejecutar_modulo_arm64


MAX_MUESTRAS = 30
CSV_NOMBRE = "entrada_sensores.csv"
CSV_PATH = ARM64_DIR / CSV_NOMBRE
CLIENT_ID_GESTOR = "gestor_datos_arm64_G8"

# Orden lógico de columnas del CSV:
# 0=id, 1=timestamp, 2=gas, 3=suelo_area1, 4=suelo_area2, 5=luz, 6=temperatura, 7=humedad_ambiental
TOPIC_A_CAMPO = {
    TOPIC_GAS: "gas",
    TOPIC_SUELO_AREA1: "suelo_area1",
    TOPIC_SUELO_AREA2: "suelo_area2",
    TOPIC_LDR: "luz",
    TOPIC_DHT_TEMP: "temperatura",
    TOPIC_DHT_HUM: "humedad_ambiental",
}

COLUMNAS_CSV = [
    "id",
    "timestamp",
    "gas",
    "suelo_area1",
    "suelo_area2",
    "luz",
    "temperatura",
    "humedad_ambiental",
]

COLUMNAS_ARM64 = {
    "gas": 2,
    "suelo_area1": 3,
    "suelo_area2": 4,
    "luz": 5,
    "temperatura": 6,
    "humedad_ambiental": 7,
}

MODULOS_A_EJECUTAR = {
    "media": 1,
    "varianza": 2,
    "anomalias": 3,
    "prediccion": 4,
    "tendencia": 5,
}

_lock = threading.Lock()
_muestras: list[dict[str, Any]] = []
_ultimos_valores: dict[str, Optional[float]] = {campo: None for campo in TOPIC_A_CAMPO.values()}
_campos_actualizados: set[str] = set()
_recoleccion_finalizada = False
_procesamiento_finalizado = False
_error_procesamiento: Optional[str] = None
_resultados_arm64: Dict[str, Any] = {
    "estado": "esperando_datos",
    "muestras_recolectadas": 0,
    "max_muestras": MAX_MUESTRAS,
    "procesado": False,
    "resultados": {},
    "error": None,
}
_cliente_mqtt: Optional[mqtt.Client] = None


def extraer_numero(payload: str) -> Optional[float]:
    """
    Extrae el primer número útil desde payloads como:
    - 'Estado: SECO | Valor: 735 | Fecha: ...'
    - '28.5'
    """
    if payload is None:
        return None

    texto = str(payload).strip()
    match_valor = re.search(r"Valor\s*:\s*(-?\d+(?:\.\d+)?)", texto, flags=re.IGNORECASE)
    if match_valor:
        return float(match_valor.group(1))

    match_numero = re.search(r"-?\d+(?:\.\d+)?", texto)
    if match_numero:
        return float(match_numero.group(0))

    return None


def _snapshot_completo() -> bool:
    return all(valor is not None for valor in _ultimos_valores.values())


def _registrar_muestra_si_corresponde() -> None:
    """
    Agrega una fila cuando ya se tienen valores para todos los sensores
    y todos los campos tuvieron al menos una actualización nueva.
    """
    global _recoleccion_finalizada

    if _recoleccion_finalizada:
        return

    if not _snapshot_completo():
        return

    if _campos_actualizados != set(_ultimos_valores.keys()):
        return

    numero = len(_muestras) + 1
    fila = {
        "id": numero,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **{campo: _ultimos_valores[campo] for campo in _ultimos_valores},
    }
    _muestras.append(fila)
    _campos_actualizados.clear()

    _resultados_arm64["muestras_recolectadas"] = len(_muestras)
    _resultados_arm64["estado"] = "recolectando"

    print(f"[GESTOR] Muestra {len(_muestras)}/{MAX_MUESTRAS} registrada en RAM.")

    if len(_muestras) == MAX_MUESTRAS:
        _recoleccion_finalizada = True
        _resultados_arm64["estado"] = "procesando_arm64"
        print("[GESTOR] Se alcanzaron exactamente 30 muestras. Iniciando ARM64...")
        threading.Thread(target=_procesar_arm64_seguro, daemon=True).start()


def _escribir_csv_temporal() -> None:
    ARM64_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=COLUMNAS_CSV)
        writer.writeheader()
        writer.writerows(_muestras)

    print(f"[GESTOR] CSV temporal creado: {CSV_PATH}")


def _procesar_arm64_seguro() -> None:
    global _procesamiento_finalizado, _error_procesamiento

    try:
        with _lock:
            _escribir_csv_temporal()

        resultados: Dict[str, Dict[str, str]] = {}

        for nombre_sensor, columna in COLUMNAS_ARM64.items():
            resultados[nombre_sensor] = {}
            for nombre_modulo, numero_modulo in MODULOS_A_EJECUTAR.items():
                stdout = ejecutar_modulo_arm64(
                    numero_modulo=numero_modulo,
                    columna=columna,
                    csv_path=CSV_PATH,
                )
                resultados[nombre_sensor][nombre_modulo] = stdout
                print(f"[ARM64] {nombre_sensor} / {nombre_modulo}: OK")

        with _lock:
            _resultados_arm64.update(
                {
                    "estado": "finalizado",
                    "procesado": True,
                    "resultados": resultados,
                    "error": None,
                    "muestras_recolectadas": MAX_MUESTRAS,
                    "fecha_procesamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            _procesamiento_finalizado = True

    except Exception as exc:
        _error_procesamiento = str(exc)
        with _lock:
            _resultados_arm64.update(
                {
                    "estado": "error",
                    "procesado": False,
                    "error": _error_procesamiento,
                }
            )
        print(f"[GESTOR] ERROR procesando ARM64: {_error_procesamiento}")

    finally:
        try:
            if CSV_PATH.exists():
                CSV_PATH.unlink()
                print("[GESTOR] CSV temporal eliminado para reducir escrituras en MicroSD.")
        except Exception as exc:
            print(f"[GESTOR] No se pudo eliminar el CSV temporal: {exc}")

        cliente = _cliente_mqtt
        if cliente is not None:
            try:
                cliente.loop_stop()
                cliente.disconnect()
                print("[GESTOR] MQTT detenido. El proceso de datos solo ocurre una vez.")
            except Exception as exc:
                print(f"[GESTOR] No se pudo cerrar MQTT limpiamente: {exc}")


def on_connect(client: mqtt.Client, userdata: Any, flags: Any, rc: int, properties: Any = None) -> None:
    if rc == 0:
        print("[GESTOR] Conectado a MQTT. Escuchando sensores para ARM64...")
        for topic in TOPIC_A_CAMPO:
            client.subscribe(topic, qos=1)
            print(f"[GESTOR] Suscrito a: {topic}")
    else:
        print(f"[GESTOR] Error de conexión MQTT. Código: {rc}")


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    if _recoleccion_finalizada:
        return

    campo = TOPIC_A_CAMPO.get(msg.topic)
    if campo is None:
        return

    payload = msg.payload.decode("utf-8", errors="ignore")
    valor = extraer_numero(payload)

    if valor is None:
        print(f"[GESTOR] Payload ignorado. No contiene número válido: {msg.topic} -> {payload}")
        return

    with _lock:
        _ultimos_valores[campo] = valor
        _campos_actualizados.add(campo)
        _registrar_muestra_si_corresponde()


def iniciar_escucha_mqtt() -> None:
    """Función objetivo para el hilo de recolección MQTT."""
    global _cliente_mqtt

    cliente = mqtt.Client(
        client_id=CLIENT_ID_GESTOR,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    _cliente_mqtt = cliente
    cliente.on_connect = on_connect
    cliente.on_message = on_message

    try:
        cliente.connect(BROKER, PORT, 60)
        cliente.loop_start()

        while not _procesamiento_finalizado and _error_procesamiento is None:
            time.sleep(0.5)

    except Exception as exc:
        with _lock:
            _resultados_arm64.update({"estado": "error", "error": str(exc)})
        print(f"[GESTOR] Error en escucha MQTT: {exc}")


def obtener_resultados_dashboard() -> Dict[str, Any]:
    """Devuelve una copia segura para el endpoint /api/dashboard."""
    with _lock:
        return dict(_resultados_arm64)