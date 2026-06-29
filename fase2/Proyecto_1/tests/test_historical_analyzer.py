#!/usr/bin/env python3
"""Pruebas aisladas del analizador histórico ARM64."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "raspberry" / "backend"
CSV_FILE = PROJECT_DIR / "raspberry" / "arm64" / "lecturas.csv"
MISSING_FILE = PROJECT_DIR / "raspberry" / "arm64" / "no_existe.csv"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from arm64_bridge import run_historical_analysis


def count_data_rows(file_path: Path) -> int:
    """Cuenta filas de datos excluyendo el encabezado."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def execute_case(
    name: str,
    file_path: Path,
    start_line: int,
    end_line: int,
    column: str,
    expected_ok: bool,
    expected_error: str | None = None,
    expected_detail: str | None = None,
) -> bool:
    print(f"\n=== {name} ===")
    result = run_historical_analysis(
        file_path=str(file_path.resolve()),
        start_line=start_line,
        end_line=end_line,
        column=column,
        module_name="historical_analyzer",
        timeout=15,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    if result.get("ok") is not expected_ok:
        print(
            f"ERROR: Se esperaba ok={expected_ok}, "
            f"pero se obtuvo ok={result.get('ok')}"
        )
        return False

    parsed = result.get("parsed")
    if not isinstance(parsed, dict):
        print("ERROR: parsed no es un diccionario.")
        return False
    if parsed.get("MODULE") != "HISTORICAL_ANALYZER":
        print("ERROR: MODULE no corresponde al analizador histórico.")
        return False

    if expected_ok:
        if parsed.get("STATUS") != "OK":
            print("ERROR: El caso válido no devolvió STATUS=OK.")
            return False
        if parsed.get("COLUMN") != column:
            print("ERROR: La columna de salida no coincide.")
            return False
        if parsed.get("WINDOW_START") != str(start_line):
            print("ERROR: WINDOW_START no coincide.")
            return False
        if parsed.get("WINDOW_END") != str(end_line):
            print("ERROR: WINDOW_END no coincide.")
            return False

        expected_count = end_line - start_line + 1
        if parsed.get("COUNT") != str(expected_count):
            print(
                f"ERROR: Se esperaba COUNT={expected_count}, "
                f"pero se obtuvo COUNT={parsed.get('COUNT')}"
            )
            return False

        for field in ("MIN", "MAX", "SUM"):
            if field not in parsed:
                print(f"ERROR: Falta {field} en la respuesta.")
                return False
    else:
        if parsed.get("STATUS") != "ERROR":
            print("ERROR: El caso inválido no devolvió STATUS=ERROR.")
            return False
        if expected_error and parsed.get("ERROR") != expected_error:
            print(
                f"ERROR: Se esperaba ERROR={expected_error}, "
                f"pero se obtuvo ERROR={parsed.get('ERROR')}"
            )
            return False
        if expected_detail and parsed.get("DETAIL") != expected_detail:
            print(
                f"ERROR: Se esperaba DETAIL={expected_detail}, "
                f"pero se obtuvo DETAIL={parsed.get('DETAIL')}"
            )
            return False

    print("OK")
    return True


def main() -> int:
    if not CSV_FILE.is_file():
        print(f"ERROR: No existe el CSV de prueba: {CSV_FILE}")
        return 1

    total_rows = count_data_rows(CSV_FILE)
    if total_rows < 10:
        print("ERROR: lecturas.csv debe contener al menos 10 filas.")
        return 1

    print(f"Filas de datos detectadas: {total_rows}")

    with tempfile.TemporaryDirectory(
        prefix="historical_analyzer_"
    ) as temporary_directory:
        no_newline_file = (
            Path(temporary_directory) / "lecturas_sin_salto_final.csv"
        )
        no_newline_file.write_bytes(CSV_FILE.read_bytes().rstrip(b"\r\n"))

        cases = [
            ("Rango válido TEMP", CSV_FILE, 1, 10, "TEMP", True, None, None),
            ("Rango válido GAS", CSV_FILE, 1, 10, "GAS", True, None, None),
            (
                "Última línea real", CSV_FILE, total_rows, total_rows,
                "TEMP", True, None, None,
            ),
            (
                "Última línea sin salto final", no_newline_file,
                total_rows, total_rows, "GAS", True, None, None,
            ),
            (
                "Final menor que inicial", CSV_FILE, 10, 5, "TEMP", False,
                "INVALID_RANGE", "END_LINE_BEFORE_START_LINE",
            ),
            (
                "Columna inexistente", CSV_FILE, 1, 10, "NO_EXISTE", False,
                "INVALID_COLUMN", "UNKNOWN_SENSOR_COLUMN",
            ),
            (
                "Archivo inexistente", MISSING_FILE, 1, 10, "TEMP", False,
                "FILE_NOT_FOUND", "INPUT_FILE_COULD_NOT_BE_OPENED",
            ),
            (
                "Inicio fuera del archivo", CSV_FILE, total_rows + 1,
                total_rows + 1, "TEMP", False, "INVALID_RANGE",
                "START_LINE_EXCEEDS_FILE_LENGTH",
            ),
            (
                "Final fuera del archivo", CSV_FILE, total_rows,
                total_rows + 1, "TEMP", False, "INVALID_RANGE",
                "END_LINE_EXCEEDS_FILE_LENGTH",
            ),
        ]

        results = [
            execute_case(
                name=name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                column=column,
                expected_ok=expected_ok,
                expected_error=expected_error,
                expected_detail=expected_detail,
            )
            for (
                name, file_path, start_line, end_line, column,
                expected_ok, expected_error, expected_detail,
            ) in cases
        ]

    if not all(results):
        print("\nERROR: Una o más pruebas históricas fallaron.")
        return 1

    print("\nOK: Todas las pruebas del analizador histórico pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
