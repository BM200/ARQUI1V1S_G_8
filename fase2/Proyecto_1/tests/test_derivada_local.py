#!/usr/bin/env python3
from __future__ import annotations

import csv
import platform
import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ARM64_DIR = ROOT_DIR / "raspberry" / "arm64"
BINARY = ARM64_DIR / "build" / "modulo_5_derivada_local"
LECTURAS = ARM64_DIR / "lecturas.csv"

COLUMN_MAP = {
    "TEMP": "TEMP",
    "HUM_AIRE": "HUM_AIRE",
    "SOIL1": "HUM_SUELO_1",
    "SOIL2": "HUM_SUELO_2",
    "LUZ": "LUZ",
    "GAS": "GAS",
}


def run_command(command, *, cwd=None, input_text=None, timeout=20):
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def compile_derivada_local():
    print("Compilando modulo_5_derivada_local...")
    result = run_command(["make", "derivada_local"], cwd=ARM64_DIR)

    print("STDOUT make:")
    print(result.stdout)

    print("STDERR make:")
    print(result.stderr)

    if result.returncode != 0:
        raise AssertionError(f"make derivada_local falló con código {result.returncode}")

    if not BINARY.exists():
        raise AssertionError(f"No se encontró el binario esperado: {BINARY}")

    print(f"OK: binario encontrado en {BINARY}")


def get_runner():
    machine = platform.machine().lower()

    if machine in {"aarch64", "arm64"}:
        return [str(BINARY)]

    qemu = shutil.which("qemu-aarch64")
    if not qemu:
        raise AssertionError(
            "Este sistema no es ARM64 nativo y no se encontró qemu-aarch64."
        )

    return [qemu, str(BINARY)]


def parse_key_value_output(output: str) -> dict[str, str]:
    parsed = {}

    for line in output.splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()

    return parsed


def trunc_div_toward_zero(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError("division by zero")

    sign = -1 if (a < 0) ^ (b < 0) else 1
    return sign * (abs(a) // abs(b))


def calculate_expected_derivative(
    csv_path: Path,
    start_line: int,
    end_line: int,
    logical_column: str,
) -> dict[str, int]:
    header_column = COLUMN_MAP[logical_column]

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    selected_rows = rows[start_line - 1 : end_line]
    ys = [int(row[header_column]) for row in selected_rows]

    window_size = 5
    slopes = []

    for index in range(0, len(ys) - window_size + 1):
        w = ys[index : index + window_size]
        sum_y = sum(w)
        sum_xy = (
            (0 * w[0])
            + (1 * w[1])
            + (2 * w[2])
            + (3 * w[3])
            + (4 * w[4])
        )

        numerator = (5 * sum_xy) - (10 * sum_y)
        slope = trunc_div_toward_zero(numerator * 100, 50)
        slopes.append(slope)

    return {
        "COUNT": len(ys),
        "WINDOW_SIZE": window_size,
        "MAX_LOCAL_SLOPE_X100": max(slopes, key=lambda value: abs(value)),
    }


def run_case(
    name: str,
    args: list[str],
    expected_texts: list[str],
    expected_code: int | None = None,
) -> subprocess.CompletedProcess[str]:
    command = get_runner() + args

    print(f"\nCaso: {name}")
    print("Comando:")
    print(" ".join(command))

    result = run_command(command, cwd=ARM64_DIR, timeout=15)

    print("STDOUT:")
    print(result.stdout)

    print("STDERR:")
    print(result.stderr)

    if expected_code is not None and result.returncode != expected_code:
        raise AssertionError(
            f"{name}: código esperado {expected_code}, obtenido {result.returncode}"
        )

    for text in expected_texts:
        if text not in result.stdout:
            raise AssertionError(f"{name}: no se encontró en stdout: {text}")

    print(f"OK: {name}")
    return result


def test_valid_derivada_local():
    start_line = 1
    end_line = 10
    column = "TEMP"

    expected = calculate_expected_derivative(
        csv_path=LECTURAS,
        start_line=start_line,
        end_line=end_line,
        logical_column=column,
    )

    result = run_case(
        name="Derivada local válida TEMP",
        args=["lecturas.csv", str(start_line), str(end_line), column],
        expected_texts=[
            "CALC=LOCAL_DERIVATIVE",
            "COLUMN=TEMP",
            "WINDOW_START=1",
            "WINDOW_END=10",
            "COUNT=10",
            "WINDOW_SIZE=5",
            f"MAX_LOCAL_SLOPE_X100={expected['MAX_LOCAL_SLOPE_X100']}",
            "STATUS=OK",
        ],
        expected_code=0,
    )

    parsed = parse_key_value_output(result.stdout)

    exact_expected = {
        "CALC": "LOCAL_DERIVATIVE",
        "COLUMN": column,
        "WINDOW_START": str(start_line),
        "WINDOW_END": str(end_line),
        "COUNT": str(expected["COUNT"]),
        "WINDOW_SIZE": str(expected["WINDOW_SIZE"]),
        "MAX_LOCAL_SLOPE_X100": str(expected["MAX_LOCAL_SLOPE_X100"]),
        "STATUS": "OK",
    }

    for key, expected_value in exact_expected.items():
        actual_value = parsed.get(key)
        if actual_value != expected_value:
            raise AssertionError(
                f"{key}: esperado {expected_value}, obtenido {actual_value}"
            )


def test_error_cases():
    run_case(
        name="archivo inexistente",
        args=["archivo_inexistente.csv", "1", "10", "TEMP"],
        expected_texts=[
            "CALC=LOCAL_DERIVATIVE",
            "STATUS=ERROR",
            "ERROR=FILE_NOT_FOUND",
            "DETAIL=INPUT_FILE_COULD_NOT_BE_OPENED",
        ],
        expected_code=1,
    )

    run_case(
        name="rango inválido",
        args=["lecturas.csv", "10", "1", "TEMP"],
        expected_texts=[
            "CALC=LOCAL_DERIVATIVE",
            "STATUS=ERROR",
            "ERROR=INVALID_RANGE",
            "DETAIL=END_LINE_BEFORE_START_LINE",
        ],
        expected_code=1,
    )

    run_case(
        name="columna inválida",
        args=["lecturas.csv", "1", "10", "NO_EXISTE"],
        expected_texts=[
            "CALC=LOCAL_DERIVATIVE",
            "STATUS=ERROR",
            "ERROR=INVALID_COLUMN",
            "DETAIL=UNKNOWN_SENSOR_COLUMN",
        ],
        expected_code=1,
    )

    run_case(
        name="datos insuficientes",
        args=["lecturas.csv", "1", "4", "TEMP"],
        expected_texts=[
            "CALC=LOCAL_DERIVATIVE",
            "STATUS=ERROR",
            "ERROR=INSUFFICIENT_DATA",
            "DETAIL=NEED_AT_LEAST_FIVE_VALUES",
        ],
        expected_code=1,
    )


def main():
    compile_derivada_local()
    test_valid_derivada_local()
    test_error_cases()
    print("\nTEST DERIVADA LOCAL: OK")


if __name__ == "__main__":
    main()
