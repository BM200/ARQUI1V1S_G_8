#!/usr/bin/env python3
"""Prueba aislada del endpoint Flask para ARM64."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = PROJECT_DIR / "invernadero_dashboard"
APP_FILE = DASHBOARD_DIR / "app.py"

SAVED_RESULTS: list[dict] = []


def install_safe_test_doubles() -> None:
    """Evita conexiones reales a MongoDB y MQTT, pero no simula ARM64."""
    fake_db = types.ModuleType("db")
    fake_db.obtener_ultimas_lecturas = lambda limite=50: []
    fake_db.obtener_ultimos_eventos = lambda limite=20: []
    fake_db.obtener_ultimos_comandos = lambda limite=20: []
    fake_db.obtener_resultados_arm64 = lambda: list(SAVED_RESULTS)
    fake_db.guardar_evento = lambda *args, **kwargs: None
    fake_db.guardar_comando = lambda *args, **kwargs: None
    fake_db.guardar_lectura = lambda *args, **kwargs: None
    fake_db.actualizar_estado_global = lambda *args, **kwargs: None

    def guardar_resultado_arm64(resultado: dict) -> bool:
        SAVED_RESULTS.append(dict(resultado))
        return True

    fake_db.guardar_resultado_arm64 = guardar_resultado_arm64

    fake_mqtt = types.ModuleType("mqtt_client")
    fake_mqtt.socketio_ref = None
    fake_mqtt.estado_actual = {
        "temperatura": "--",
        "humedad_ambiente": "--",
        "humedad_suelo_area1": "--",
        "humedad_suelo_area2": "--",
        "luz": "--",
        "gas": "--",
        "estado_global": "DESCONECTADO",
        "riego": "OFF",
        "ventilador": "OFF",
        "luces": "OFF",
        "alarma": "OFF",
        "ultima_actualizacion": "--",
    }
    fake_mqtt.publicar_comando = lambda accion, valor: True
    fake_mqtt.iniciar_mqtt = lambda: None

    sys.modules["db"] = fake_db
    sys.modules["mqtt_client"] = fake_mqtt


def load_dashboard_module():
    if not APP_FILE.is_file():
        raise FileNotFoundError(f"No existe app.py: {APP_FILE}")

    if str(DASHBOARD_DIR) not in sys.path:
        sys.path.insert(0, str(DASHBOARD_DIR))

    install_safe_test_doubles()

    spec = importlib.util.spec_from_file_location(
        "invernadero_dashboard_arm64_endpoint_test",
        APP_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo preparar la importación de app.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("=== PRUEBA DEL ENDPOINT ARM64 ===")
    print("MongoDB: simulado en memoria")
    print("MQTT: simulado")
    print("ARM64: servicio y bridge reales")
    print("Hardware y GPIO: no utilizados")

    try:
        dashboard_module = load_dashboard_module()
    except Exception as exc:
        print(f"ERROR: No se pudo cargar Flask: {type(exc).__name__}: {exc}")
        return 1

    app = getattr(dashboard_module, "app", None)

    if app is None:
        print("ERROR: app.py no expone la aplicación Flask.")
        return 1

    client = app.test_client()

    response = client.post(
        "/api/arm64/fase1/run",
        json={
            "module_number": 3,
            "column": 2,
        },
    )

    payload = response.get_json(silent=True)

    print(f"HTTP status: {response.status_code}")
    print("Respuesta:")
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    if response.status_code != 200:
        print("ERROR: El endpoint no respondió HTTP 200.")
        return 1

    if not isinstance(payload, dict):
        print("ERROR: La respuesta no es un objeto JSON.")
        return 1

    if payload.get("ok") is not True:
        print("ERROR: La respuesta no contiene ok=true.")
        return 1

    if payload.get("saved") is not True:
        print("ERROR: La respuesta no contiene saved=true.")
        return 1

    data = payload.get("data")

    if not isinstance(data, dict):
        print("ERROR: data no es un diccionario.")
        return 1

    parsed = data.get("parsed")

    if not isinstance(parsed, dict) or not parsed.get("MODULE"):
        print("ERROR: data.parsed.MODULE no existe.")
        return 1

    if len(SAVED_RESULTS) != 1:
        print("ERROR: El resultado no pasó por guardar_resultado_arm64().")
        return 1

    print(f"MODULE={parsed['MODULE']}")
    print("OK: El endpoint ejecutó ARM64 y solicitó guardar el resultado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
