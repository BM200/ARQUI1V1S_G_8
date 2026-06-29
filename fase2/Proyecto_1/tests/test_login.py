#!/usr/bin/env python3
"""Prueba aislada del login y protección de rutas Flask."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = PROJECT_DIR / "invernadero_dashboard"
APP_FILE = DASHBOARD_DIR / "app.py"

TEST_USER = "testadmin"
TEST_PASSWORD = "testpassword"

os.environ["DASHBOARD_USER"] = TEST_USER
os.environ["DASHBOARD_PASSWORD"] = TEST_PASSWORD
os.environ["DASHBOARD_SECRET_KEY"] = "test-secret-key-for-login"


def install_safe_test_doubles() -> None:
    """Evita conexiones reales a MongoDB y MQTT."""
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
    if str(DASHBOARD_DIR) not in sys.path:
        sys.path.insert(0, str(DASHBOARD_DIR))

    install_safe_test_doubles()

    spec = importlib.util.spec_from_file_location(
        "invernadero_dashboard_login_test",
        APP_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar app.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def redirects_to_login(response) -> bool:
    return (
        response.status_code == 302
        and response.headers.get("Location", "").endswith("/login")
    )


def main() -> int:
    dashboard = load_dashboard_module()
    client = dashboard.app.test_client()

    response = client.get("/")
    if not redirects_to_login(response):
        print("ERROR: GET / sin sesión no redirigió a /login.")
        return 1

    protected_requests = [
        client.post("/api/comando", json={"accion": "luces", "valor": "ON"}),
        client.post("/api/modo", json={"modo": "AUTO"}),
        client.post(
            "/api/arm64/fase1/run",
            json={"module_number": 3, "column": 2},
        ),
    ]

    if not all(redirects_to_login(response) for response in protected_requests):
        print("ERROR: Uno o más endpoints POST no están protegidos.")
        return 1

    response = client.post(
        "/login",
        data={"username": TEST_USER, "password": "incorrecta"},
    )

    if response.status_code != 401:
        print("ERROR: El login incorrecto no fue rechazado.")
        return 1

    response = client.post(
        "/login",
        data={"username": TEST_USER, "password": TEST_PASSWORD},
    )

    if response.status_code != 302:
        print("ERROR: El login correcto no creó la sesión.")
        return 1

    response = client.get("/")

    if response.status_code != 200:
        print("ERROR: El dashboard no abrió después del login.")
        return 1

    response = client.get("/logout")

    if not redirects_to_login(response):
        print("ERROR: /logout no redirigió a /login.")
        return 1

    response = client.get("/")

    if not redirects_to_login(response):
        print("ERROR: La sesión siguió activa después de logout.")
        return 1

    print("OK: Login, logout y protección de rutas funcionan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
