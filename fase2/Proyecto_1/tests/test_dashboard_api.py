#!/usr/bin/env python3
"""Prueba segura de carga y endpoints del dashboard Flask."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = PROJECT_DIR / "invernadero_dashboard"
APP_FILE = DASHBOARD_DIR / "app.py"

os.environ["DASHBOARD_USER"] = "testadmin"
os.environ["DASHBOARD_PASSWORD"] = "testpassword"
os.environ["DASHBOARD_SECRET_KEY"] = "test-secret-key-for-dashboard-api"

EXPECTED_GET_ENDPOINTS = [
    "/login",
    "/",
    "/api/estado",
    "/api/lecturas",
    "/api/eventos",
    "/api/comandos",
    "/api/arm64",
]

RECOMMENDED_ENDPOINTS = [
    ("GET", "/api/status"),
    ("GET", "/api/readings/recent"),
    ("GET", "/api/arm64/results"),
    ("POST", "/api/arm64/fase1/run"),
    ("POST", "/api/arm64/historical/run"),
    ("POST", "/api/control"),
]

EXPECTED_UNCALLED_ENDPOINTS = [
    ("POST", "/api/arm64/fase1/run"),
    ("POST", "/api/arm64/historical/run"),
    ("POST", "/api/comando"),
    ("POST", "/api/modo"),
    ("GET", "/login"),
    ("GET", "/logout"),
]


def install_safe_test_doubles() -> None:
    """Instala dobles para impedir conexiones reales a MongoDB y MQTT."""
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
    fake_db.guardar_resultado_historico_arm64 = lambda resultado: True

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
        raise FileNotFoundError(f"No existe el dashboard Flask: {APP_FILE}")

    sys.path.insert(0, str(DASHBOARD_DIR))
    install_safe_test_doubles()

    spec = importlib.util.spec_from_file_location(
        "invernadero_dashboard_test_app",
        APP_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo preparar la importación de app.py")

    module = importlib.util.module_from_spec(spec)
    # Flask consulta sys.modules y el __spec__ del módulo para calcular
    # root_path. Registrarlo antes de ejecutar permite encontrar las carpetas
    # templates/ y static/ ubicadas junto a app.py.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("=== PRUEBA SEGURA DEL DASHBOARD FLASK ===")
    print("MongoDB: simulado")
    print("MQTT: simulado")
    print("GPIO y actuadores: no importados")

    try:
        dashboard_module = load_dashboard_module()
    except ImportError as exc:
        print(f"ERROR: Falta una dependencia del dashboard: {exc}")
        return 1
    except Exception as exc:
        print(f"ERROR: Flask no pudo cargar app.py: {type(exc).__name__}: {exc}")
        return 1

    app = getattr(dashboard_module, "app", None)
    if app is None:
        print("ERROR: app.py no expone una aplicación Flask llamada 'app'.")
        return 1

    print("OK: La aplicación Flask fue creada correctamente.")

    client = app.test_client()
    failures: list[str] = []

    for endpoint in EXPECTED_GET_ENDPOINTS:
        try:
            response = client.get(endpoint)
            if 200 <= response.status_code < 400:
                print(f"OK: GET {endpoint} -> {response.status_code}")
            else:
                print(f"ERROR: GET {endpoint} -> {response.status_code}")
                failures.append(endpoint)
        except Exception as exc:
            print(f"ERROR: GET {endpoint} lanzó {type(exc).__name__}: {exc}")
            failures.append(endpoint)

    existing_routes = {
        rule.rule: sorted(
            method for method in rule.methods if method not in {"HEAD", "OPTIONS"}
        )
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
    }

    print("\nEndpoints Flask detectados:")
    for route, methods in sorted(existing_routes.items()):
        print(f"- {','.join(methods)} {route}")

    print("\nEndpoints detectados sin ejecutarlos:")
    for method, route in EXPECTED_UNCALLED_ENDPOINTS:
        methods = existing_routes.get(route, [])
        if method in methods:
            print(f"OK: {method} {route}")
        else:
            print(f"ERROR: No existe {method} {route}")
            failures.append(route)

    print("\nEndpoints recomendados que todavía no existen:")
    missing_recommended = []

    for method, route in RECOMMENDED_ENDPOINTS:
        methods = existing_routes.get(route, [])
        if method not in methods:
            missing_recommended.append((method, route))
            print(f"- {method} {route}")

    if not missing_recommended:
        print("- Ninguno")

    if failures:
        print(f"\nERROR: Fallaron {len(failures)} endpoints existentes.")
        return 1

    print("\nOK: El dashboard Flask carga y sus endpoints GET responden.")
    print("NOTA: La prueba no abrió un puerto TCP ni conectó servicios externos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
