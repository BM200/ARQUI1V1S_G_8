#!/usr/bin/env python3
"""Servicio del dashboard para ejecutar módulos ARM64."""

from __future__ import annotations

import importlib.util
import csv
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
ARM64_DIR = PROJECT_DIR / "raspberry" / "arm64"
ARM64_CSV = ARM64_DIR / "lecturas.csv"
ARM64_CSV_HEADER = "TEMP,HUM_AIRE,SOIL1,SOIL2,LUZ,GAS"
ARM64_OLD_CSV_HEADER = "ID,TEMP,HUM_AIRE,HUM_SUELO_1,HUM_SUELO_2,LUZ,GAS,RIEGO_1,RIEGO_2"
ARM64_CSV_COLUMNS = ARM64_CSV_HEADER.split(",")
ARM64_OLD_TO_NEW_COLUMNS = {
    "TEMP": "TEMP",
    "HUM_AIRE": "HUM_AIRE",
    "HUM_SUELO_1": "SOIL1",
    "HUM_SUELO_2": "SOIL2",
    "LUZ": "LUZ",
    "GAS": "GAS",
}


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


def _resolve_arm64_csv(file_path: str | Path | None) -> Path:
    raw_path = str(file_path or "lecturas.csv").strip() or "lecturas.csv"
    path = Path(raw_path).expanduser()

    if path.is_absolute():
        return path.resolve()

    if raw_path == "lecturas.csv":
        return ARM64_CSV.resolve()

    candidates = [
        ARM64_DIR / path,
        PROJECT_DIR.parent / path,
        PROJECT_DIR / path,
    ]

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved

    return candidates[0].resolve()


def _migrate_old_arm64_csv(csv_path: Path) -> dict[str, Any] | None:
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            rows = [
                {
                    new_name: (row.get(old_name) or "").strip()
                    for old_name, new_name in ARM64_OLD_TO_NEW_COLUMNS.items()
                }
                for row in reader
            ]

        with csv_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=ARM64_CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        print(f"[ARM64 CSV] CSV viejo migrado a formato único: {csv_path}")
        return None
    except OSError as exc:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "CSV_MIGRATION_FAILED",
            "detail": f"No se pudo migrar el CSV ARM64 viejo: {exc}",
            "file_path": str(csv_path),
        }


def _validate_arm64_csv(file_path: str | Path | None) -> dict[str, Any] | None:
    csv_path = _resolve_arm64_csv(file_path)

    if not csv_path.is_file():
        print(f"[ARM64] CSV rechazado: no existe {csv_path}")
        return {
            "ok": False,
            "status": "ERROR",
            "error": "CSV_NOT_FOUND",
            "detail": (
                "No existe el CSV ARM64 real. Ejecuta main.py para regenerar "
                f"{ARM64_CSV}."
            ),
            "file_path": str(csv_path),
        }

    try:
        with csv_path.open("r", encoding="utf-8-sig") as archivo:
            header = archivo.readline().strip()
    except OSError as exc:
        print(f"[ARM64] CSV rechazado: no se pudo leer {csv_path}: {exc}")
        return {
            "ok": False,
            "status": "ERROR",
            "error": "CSV_READ_FAILED",
            "detail": f"No se pudo leer el CSV ARM64: {exc}",
            "file_path": str(csv_path),
        }

    if header == ARM64_OLD_CSV_HEADER:
        migration_error = _migrate_old_arm64_csv(csv_path)
        if migration_error:
            return migration_error
        header = ARM64_CSV_HEADER

    if header != ARM64_CSV_HEADER:
        print(f"[ARM64] CSV rechazado por encabezado inválido: {header!r}")
        return {
            "ok": False,
            "status": "ERROR",
            "error": "CSV_HEADER_INVALID",
            "detail": (
                f"El CSV ARM64 debe usar exactamente: {ARM64_CSV_HEADER}."
            ),
            "file_path": str(csv_path),
            "header": header,
        }

    return None


def execute_fase1_module(
    module_number: int,
    column: int | str = 2,
    file_path: str = "lecturas.csv",
    start_line: int | str = 1,
    end_line: int | str = 30,
) -> dict[str, Any]:
    """Ejecuta un módulo migrado sin propagar excepciones a Flask."""
    try:
        csv_error = _validate_arm64_csv(file_path)
        if csv_error:
            return csv_error

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
        csv_error = _validate_arm64_csv(file_path)
        if csv_error:
            return csv_error

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
    ideal: int | str = 25,
    k: int | str = 10,
) -> dict[str, Any]:
    """Ejecuta el analizador histórico real sin propagar excepciones."""
    try:
        csv_error = _validate_arm64_csv(file_path)
        if csv_error:
            return csv_error

        bridge = _load_bridge()
        result = bridge.run_historical_analysis(
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            column=column,
            ideal=ideal,
            k=k,
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
