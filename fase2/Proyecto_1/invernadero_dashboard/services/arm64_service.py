#!/usr/bin/env python3
"""Servicio del dashboard para ejecutar módulos ARM64."""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any


SERVICE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = SERVICE_DIR.parent
PROJECT_DIR = DASHBOARD_DIR.parent
BRIDGE_FILE = PROJECT_DIR / "raspberry" / "backend" / "arm64_bridge.py"
BRIDGE_MODULE_NAME = "invernadero_arm64_bridge"


@lru_cache(maxsize=1)
def _load_bridge() -> ModuleType:
    """Carga arm64_bridge.py desde su ruta real."""
    if not BRIDGE_FILE.is_file():
        raise FileNotFoundError(f"No existe el bridge ARM64: {BRIDGE_FILE}")

    spec = importlib.util.spec_from_file_location(
        BRIDGE_MODULE_NAME,
        BRIDGE_FILE,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el bridge ARM64: {BRIDGE_FILE}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def execute_fase1_module(
    module_number: int,
    column: int | str = 2,
    file_path: str = "lecturas.csv",
    start_line: int | str = 1,
    end_line: int | str = 30,
) -> dict[str, Any]:
    """Ejecuta un módulo migrado sin propagar excepciones a Flask."""
    try:
        bridge = _load_bridge()
        result = bridge.run_fase1_module(
            module_number=module_number,
            column=column,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
        )

        if not isinstance(result, dict):
            return {
                "ok": False,
                "status": "ERROR",
                "error": "INVALID_BRIDGE_RESPONSE",
                "detail": "arm64_bridge returned a non-dictionary response",
            }

        return result

    except Exception as exc:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "ARM64_SERVICE_ERROR",
            "detail": f"{type(exc).__name__}: {exc}",
            "module_number": module_number,
            "column": column,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
        }


def execute_fase2_module(
    module_number: int | None = None,
    module_name: str | None = None,
    file_path: str = "lecturas.csv",
    start_line: int | str = 1,
    end_line: int | str = 30,
    column: str = "TEMP",
    ideal: int | str = 25,
    k: int | str = 5,
) -> dict[str, Any]:
    """Ejecuta un módulo avanzado de Fase 2 sin propagar excepciones."""
    try:
        bridge = _load_bridge()
        result = bridge.run_fase2_module(
            module_number=module_number,
            module_name=module_name,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            column=column,
            ideal=ideal,
            k=k,
        )

        if not isinstance(result, dict):
            return {
                "ok": False,
                "status": "ERROR",
                "error": "INVALID_BRIDGE_RESPONSE",
                "detail": "arm64_bridge returned a non-dictionary response",
            }

        return result

    except Exception as exc:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "ARM64_SERVICE_ERROR",
            "detail": f"{type(exc).__name__}: {exc}",
            "module_number": module_number,
            "module_name": module_name,
            "column": column,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
        }


def execute_historical_analysis(
    file_path: str,
    start_line: int,
    end_line: int,
    column: str,
) -> dict[str, Any]:
    """Ejecuta el analizador histórico real sin propagar excepciones."""
    try:
        bridge = _load_bridge()
        result = bridge.run_historical_analysis(
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            column=column,
            module_name="historical_analyzer",
        )

        if not isinstance(result, dict):
            return {
                "ok": False,
                "status": "ERROR",
                "error": "INVALID_BRIDGE_RESPONSE",
                "detail": "arm64_bridge returned a non-dictionary response",
                "file_path": str(file_path),
                "start_line": start_line,
                "end_line": end_line,
                "column": column,
            }

        return result

    except Exception as exc:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "ARM64_SERVICE_ERROR",
            "detail": f"{type(exc).__name__}: {exc}",
            "file_path": str(file_path),
            "start_line": start_line,
            "end_line": end_line,
            "column": column,
        }
