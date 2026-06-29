#!/usr/bin/env python3
from __future__ import annotations

import csv
import platform
import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ARM64_DIR = ROOT_DIR / "raspberry" / "arm64"
BINARY = ARM64_DIR / "build" / "modulo_3_prediccion"
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


def compile_prediccion():
    print("Compilando modulo_3_prediccion...")
    result = run_command(["make", "prediccion"], cwd=ARM64_DIR)

    print("STDOUT make:")
    print(result.stdout)

    print("STDERR make:")
    print(result.stderr)

    if result.returncode != 0:
        raise AssertionError(f"make prediccion falló con código {result.returncode}")

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


def trunc_div_toward_zero(numerator: int, denominator: int) -> int:
    if denominator == 0:
        raise ZeroDivisionError("denominator is zero")

    sign = -1 if (numerator < 0) ^ (denominator < 0) else 1
    return sign * (abs(numerator) // abs(denominator))


def calculate_expected_prediction(
    csv_path: Path,
    start_line: int,
    end_line: int,
    logical_column: str,
    k: int,
) -> dict[str, int]:
    header_column = COLUMN_MAP[logical_column]

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    selected_rows = rows[start_line - 1 : end_line]
    ys = [int(row[header_column]) for row in selected_rows]
    xs = list(range(1, len(ys) + 1))

    count = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)

    numerator = (count * sum_xy) - (sum_x * sum_y)
    denominator = (count * sum_xx) - (sum_x * sum_x)

    slope_x100 = trunc_div_toward_zero(numerator * 100, denominator)
    intercept_x100 = trunc_div_toward_zero(
        (sum_y * 100) - (slope_x100 * sum_x),
        count,
    )

    x_future = count + k
    predicted = trunc_div_toward_zero(
        (slope_x100 * x_future) + intercept_x100,
        100,
    )

    return {
        "COUNT": count,
        "K": k,
        "SLOPE_X100": slope_x100,
        "INTERCEPT_X100": intercept_x100,
        f"PREDICTED_{k}": predicted,
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


def assert_prediction_output(
    result: subprocess.CompletedProcess[str],
    *,
    column: str,
    start_line: int,
    end_line: int,
    expected: dict[str, int],
):
    parsed = parse_key_value_output(result.stdout)
    k = expected["K"]
    predicted_key = f"PREDICTED_{k}"

    exact_expected = {
        "CALC": "PREDICTION",
        "COLUMN": column,
        "WINDOW_START": str(start_line),
        "WINDOW_END": str(end_line),
        "COUNT": str(expected["COUNT"]),
        "K": str(expected["K"]),
        "SLOPE_X100": str(expected["SLOPE_X100"]),
        "INTERCEPT_X100": str(expected["INTERCEPT_X100"]),
        predicted_key: str(expected[predicted_key]),
        "STATUS": "OK",
    }

    for key, expected_value in exact_expected.items():
        actual_value = parsed.get(key)
        if actual_value != expected_value:
            raise AssertionError(
                f"{key}: esperado {expected_value}, obtenido {actual_value}"
            )


def test_valid_prediction_with_explicit_k():
    start_line = 1
    end_line = 10
    column = "TEMP"
    k = 5

    expected = calculate_expected_prediction(
        csv_path=LECTURAS,
        start_line=start_line,
        end_line=end_line,
        logical_column=column,
        k=k,
    )

    predicted_key = f"PREDICTED_{k}"

    result = run_case(
        name="Predicción válida TEMP con K explícito",
        args=["lecturas.csv", str(start_line), str(end_line), column, str(k)],
        expected_texts=[
            "CALC=PREDICTION",
            "COLUMN=TEMP",
            "WINDOW_START=1",
            "WINDOW_END=10",
            "COUNT=10",
            "K=5",
            f"SLOPE_X100={expected['SLOPE_X100']}",
            f"INTERCEPT_X100={expected['INTERCEPT_X100']}",
            f"{predicted_key}={expected[predicted_key]}",
            "STATUS=OK",
        ],
        expected_code=0,
    )

    assert_prediction_output(
        result,
        column=column,
        start_line=start_line,
        end_line=end_line,
        expected=expected,
    )


def test_valid_prediction_with_explicit_k_3():
    start_line = 1
    end_line = 10
    column = "TEMP"
    k = 3

    expected = calculate_expected_prediction(
        csv_path=LECTURAS,
        start_line=start_line,
        end_line=end_line,
        logical_column=column,
        k=k,
    )

    predicted_key = f"PREDICTED_{k}"

    result = run_case(
        name="Predicción válida TEMP con K explícito 3",
        args=["lecturas.csv", str(start_line), str(end_line), column, str(k)],
        expected_texts=[
            "CALC=PREDICTION",
            "COLUMN=TEMP",
            "WINDOW_START=1",
            "WINDOW_END=10",
            "COUNT=10",
            "K=3",
            f"SLOPE_X100={expected['SLOPE_X100']}",
            f"INTERCEPT_X100={expected['INTERCEPT_X100']}",
            f"{predicted_key}={expected[predicted_key]}",
            "STATUS=OK",
        ],
        expected_code=0,
    )

    assert_prediction_output(
        result,
        column=column,
        start_line=start_line,
        end_line=end_line,
        expected=expected,
    )


def test_valid_prediction_with_default_k():
    start_line = 1
    end_line = 10
    column = "TEMP"
    k = 5

    expected = calculate_expected_prediction(
        csv_path=LECTURAS,
        start_line=start_line,
        end_line=end_line,
        logical_column=column,
        k=k,
    )

    predicted_key = f"PREDICTED_{k}"

    result = run_case(
        name="Predicción válida TEMP con K por defecto",
        args=["lecturas.csv", str(start_line), str(end_line), column],
        expected_texts=[
            "CALC=PREDICTION",
            "COLUMN=TEMP",
            "WINDOW_START=1",
            "WINDOW_END=10",
            "COUNT=10",
            "K=5",
            f"SLOPE_X100={expected['SLOPE_X100']}",
            f"INTERCEPT_X100={expected['INTERCEPT_X100']}",
            f"{predicted_key}={expected[predicted_key]}",
            "STATUS=OK",
        ],
        expected_code=0,
    )

    assert_prediction_output(
        result,
        column=column,
        start_line=start_line,
        end_line=end_line,
        expected=expected,
    )


def test_error_cases():
    run_case(
        name="archivo inexistente",
        args=["archivo_inexistente.csv", "1", "10", "TEMP", "5"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=FILE_NOT_FOUND",
            "DETAIL=INPUT_FILE_COULD_NOT_BE_OPENED",
        ],
        expected_code=1,
    )

    run_case(
        name="rango inválido",
        args=["lecturas.csv", "10", "1", "TEMP", "5"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=INVALID_RANGE",
            "DETAIL=END_LINE_BEFORE_START_LINE",
        ],
        expected_code=1,
    )

    run_case(
        name="columna inválida",
        args=["lecturas.csv", "1", "10", "NO_EXISTE", "5"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=INVALID_COLUMN",
            "DETAIL=UNKNOWN_SENSOR_COLUMN",
        ],
        expected_code=1,
    )

    run_case(
        name="datos insuficientes",
        args=["lecturas.csv", "1", "1", "TEMP", "5"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=INSUFFICIENT_DATA",
            "DETAIL=NEED_AT_LEAST_TWO_VALUES",
        ],
        expected_code=1,
    )

    run_case(
        name="K inválido no numérico",
        args=["lecturas.csv", "1", "10", "TEMP", "abc"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=INVALID_K",
            "DETAIL=K_MUST_BE_POSITIVE_INTEGER",
        ],
        expected_code=1,
    )

    run_case(
        name="K inválido cero",
        args=["lecturas.csv", "1", "10", "TEMP", "0"],
        expected_texts=[
            "CALC=PREDICTION",
            "STATUS=ERROR",
            "ERROR=INVALID_K",
            "DETAIL=K_MUST_BE_POSITIVE_INTEGER",
        ],
        expected_code=1,
    )


def main():
    compile_prediccion()
    test_valid_prediction_with_explicit_k()
    test_valid_prediction_with_explicit_k_3()
    test_valid_prediction_with_default_k()
    test_error_cases()
    print("\nTEST PREDICCION: OK")


if __name__ == "__main__":
    main()
