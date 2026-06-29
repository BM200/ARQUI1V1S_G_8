#!/usr/bin/env python3
"""Prueba aislada del puente Python ↔ ARM64."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "raspberry" / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from arm64_bridge import run_fase1_module
except ImportError as exc:
    print(f"ERROR: No se pudo importar arm64_bridge.py: {exc}")
    sys.exit(1)


def main() -> int:
    print("=== PRUEBA DEL PUENTE ARM64 ===")
    print("Módulo: 3 - Detección de anomalías")
    print("Columna: 2")
    print("MongoDB: no utilizado")
    print("Dashboard: no utilizado")
    print("Hardware y GPIO: no utilizados")

    result = run_fase1_module(3, column=2)

    print("\nResultado estructurado:")
    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    if result.get("ok") is not True:
        print("\nERROR: run_fase1_module no devolvió ok=true.")
        print(f"Detalle: {result.get('detail', 'Sin detalle')}")
        return 1

    parsed = result.get("parsed")

    if not isinstance(parsed, dict):
        print("\nERROR: parsed no es un diccionario.")
        return 1

    if not parsed.get("MODULE"):
        print("\nERROR: La salida parseada no contiene MODULE.")
        return 1

    print(f"\nMODULE={parsed['MODULE']}")
    print("OK: El puente ejecutó y procesó el módulo ARM64 correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
