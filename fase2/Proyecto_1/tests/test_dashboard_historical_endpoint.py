#!/usr/bin/env python3
"""Prueba aislada del endpoint histórico con ARM64 real."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PROJECT_DIR = TEST_FILE.parents[1]
DASHBOARD_DIR = PROJECT_DIR / "invernadero_dashboard"
APP_FILE = DASHBOARD_DIR / "app.py"

SAVED_RESULTS: list[dict] = []


def install_fake_mqtt_module() -> None:
    """Simula MQTT sin importar ni iniciar clientes reales."""
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
    sys.modules["mqtt_client"] = fake_mqtt


def install_fake_db_module() -> None:
    """Simula MongoDB en memoria sin sustituir el servicio ARM64."""
    fake_db = types.ModuleType("db")
    fake_db.obtener_ultimas_lecturas = lambda limite=50: []
    fake_db.obtener_ultimos_eventos = lambda limite=20: []
    fake_db.obtener_ultimos_comandos = lambda limite=20: []
    fake_db.obtener_resultados_arm64 = lambda: []
    fake_db.guardar_evento = lambda *args, **kwargs: None
    fake_db.guardar_comando = lambda *args, **kwargs: None
    fake_db.guardar_lectura = lambda *args, **kwargs: None
    fake_db.actualizar_estado_global = lambda *args, **kwargs: None
    fake_db.guardar_resultado_arm64 = lambda resultado: True

    def guardar_resultado_historico_arm64(resultado: dict) -> bool:
        SAVED_RESULTS.append(dict(resultado))
        return True

    fake_db.guardar_resultado_historico_arm64 = (
        guardar_resultado_historico_arm64
    )
    sys.modules["db"] = fake_db


def load_flask_app():
    os.environ["DASHBOARD_USER"] = "testadmin"
    os.environ["DASHBOARD_PASSWORD"] = "testpassword"
    os.environ["DASHBOARD_SECRET_KEY"] = "test-historical-secret-key"

    if str(DASHBOARD_DIR) not in sys.path:
        sys.path.insert(0, str(DASHBOARD_DIR))

    install_fake_mqtt_module()
    install_fake_db_module()

    module_name = "dashboard_historical_endpoint_test_app"
    spec = importlib.util.spec_from_file_location(module_name, APP_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {APP_FILE}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.app


def authenticate(client) -> None:
    """Crea una sesión autenticada para probar la ruta protegida."""
    with client.session_transaction() as flask_session:
        flask_session["authenticated"] = True
        flask_session["username"] = "testadmin"


def main() -> int:
    print("=== PRUEBA DEL ENDPOINT HISTÓRICO ARM64 ===")
    print("Flask: aplicación de prueba")
    print("MongoDB: simulado en memoria")
    print("MQTT: simulado")
    print("ARM64, servicio y bridge: reales")
    print("Hardware y GPIO: no utilizados")

    try:
        app = load_flask_app()
    except Exception as exc:
        print(f"ERROR: No se pudo cargar Flask: {type(exc).__name__}: {exc}")
        return 1

    app.config.update(TESTING=True)
    client = app.test_client()
    authenticate(client)

    response = client.post(
        "/api/arm64/historical/run",
        json={
            "file_path": "Proyecto_1/raspberry/arm64/lecturas.csv",
            "start_line": 1,
            "end_line": 10,
            "column": "TEMP",
        },
    )
    payload = response.get_json(silent=True)

    print(f"HTTP status: {response.status_code}")
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    if response.status_code != 200:
        print("ERROR: El endpoint no respondió HTTP 200.")
        return 1

    if not isinstance(payload, dict):
        print("ERROR: La respuesta no es un objeto JSON.")
        return 1

    if payload.get("ok") is not True or payload.get("saved") is not True:
        print("ERROR: La respuesta no contiene ok=true y saved=true.")
        return 1

    data = payload.get("data", {})
    parsed = data.get("parsed", {}) if isinstance(data, dict) else {}

    if parsed.get("MODULE") != "HISTORICAL_ANALYZER":
        print("ERROR: data.parsed.MODULE no es HISTORICAL_ANALYZER.")
        return 1

    if parsed.get("STATUS") != "OK":
        print("ERROR: data.parsed.STATUS no es OK.")
        return 1

    if str(parsed.get("COUNT")) != "10":
        print(f"ERROR: COUNT inesperado: {parsed.get('COUNT')}")
        return 1

    if len(SAVED_RESULTS) != 1:
        print("ERROR: El resultado no pasó una vez por el guardado simulado.")
        return 1

    print("OK: Flask ejecutó ARM64 real y solicitó guardar el resultado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
