#!/usr/bin/env python3
"""Prueba aislada de compilación y ejecución de un módulo ARM64."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
ARM64_DIR = PROJECT_DIR / "raspberry" / "arm64"
MAKEFILE = ARM64_DIR / "Makefile"
BUILD_DIR = ARM64_DIR / "build"
RESULTS_DIR = ARM64_DIR / "resultados_arm64"

MODULES = {
    "1": ("modulo_1_media", "resultado_media.txt"),
    "2": ("modulo_2_varianza", "resultado_varianza.txt"),
    "3": ("modulo_3_anomalias", "resultado_anomalias.txt"),
    "4": ("modulo_4_prediccion", "resultado_prediccion.txt"),
    "5": ("modulo_5_tendencia", "resultado_tendencia.txt"),
}


def show_process_result(
    label: str, result: subprocess.CompletedProcess[str]
) -> None:
    print(f"\n--- {label} ---")
    print(f"Código de salida: {result.returncode}")
    print("STDOUT:")
    print(result.stdout.strip() or "(vacío)")
    print("STDERR:")
    print(result.stderr.strip() or "(vacío)")


def run_command(
    command: list[str], cwd: Path, timeout: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def find_module_binaries() -> list[Path]:
    """Busca módulos tanto en build/ como en la raíz de arm64/."""
    found: set[Path] = set()

    for directory in (BUILD_DIR, ARM64_DIR):
        if not directory.is_dir():
            continue

        for candidate in directory.glob("modulo_*"):
            if candidate.is_file() and candidate.suffix != ".s":
                found.add(candidate.resolve())

    return sorted(found, key=lambda path: str(path))


def find_selected_binary(module_name: str) -> Path | None:
    """Prioriza build/modulo_X y luego arm64/modulo_X."""
    candidates = (
        BUILD_DIR / module_name,
        ARM64_DIR / module_name,
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


def main() -> int:
    module_number = os.getenv("ARM64_TEST_MODULE", "3")
    column = os.getenv("ARM64_TEST_COLUMN", "2")

    if module_number not in MODULES:
        print(f"ERROR: ARM64_TEST_MODULE debe estar entre 1 y 5: {module_number}")
        return 1

    module_name, result_name = MODULES[module_number]
    result_file = RESULTS_DIR / result_name

    print("=== PRUEBA ARM64 AISLADA ===")
    print(f"Directorio ARM64: {ARM64_DIR}")
    print(f"Módulo: {module_name}")
    print(f"Columna: {column}")
    print(f"Arquitectura anfitriona: {platform.machine()}")

    if not ARM64_DIR.is_dir():
        print(f"ERROR: No existe el directorio ARM64: {ARM64_DIR}")
        return 1

    if not MAKEFILE.is_file():
        print(f"ERROR: No existe el Makefile: {MAKEFILE}")
        return 1

    if shutil.which("make") is None:
        print("ERROR: No se encontró el comando 'make'.")
        return 1

    try:
        compile_result = run_command(["make", "all"], ARM64_DIR, timeout=60)
    except subprocess.TimeoutExpired:
        print("ERROR: La compilación excedió 60 segundos.")
        return 1
    except OSError as exc:
        print(f"ERROR: No se pudo iniciar make: {exc}")
        return 1

    show_process_result("COMPILACIÓN", compile_result)

    print("\nBinarios encontrados después de make all:")
    found_binaries = find_module_binaries()
    if found_binaries:
        for found_binary in found_binaries:
            print(f"- {found_binary}")
    else:
        print("- Ninguno")

    if compile_result.returncode != 0:
        print("ERROR: make terminó con error.")
        return 1

    binary = find_selected_binary(module_name)
    if binary is None:
        print(
            "ERROR: No se encontró el binario esperado en ninguna ubicación:"
        )
        print(f"- {BUILD_DIR / module_name}")
        print(f"- {ARM64_DIR / module_name}")
        return 1

    print(f"Binario seleccionado: {binary}")

    # Los módulos actuales escriben archivos en este directorio.
    RESULTS_DIR.mkdir(exist_ok=True)

    architecture = platform.machine().lower()
    if architecture in {"aarch64", "arm64"}:
        command = [str(binary), column]
        execution_mode = "ARM64 nativo"
    else:
        qemu = shutil.which("qemu-aarch64")
        if qemu is None:
            print(
                "ERROR: El equipo no es ARM64 y no está instalado qemu-aarch64."
            )
            return 1
        command = [qemu, str(binary), column]
        execution_mode = "QEMU"

    previous_mtime = result_file.stat().st_mtime_ns if result_file.exists() else None

    print(f"\nModo de ejecución: {execution_mode}")
    print(f"Comando: {' '.join(command)}")

    try:
        execution_result = run_command(command, ARM64_DIR, timeout=10)
    except subprocess.TimeoutExpired as exc:
        print("ERROR: La ejecución ARM64 excedió 10 segundos.")
        if exc.stdout:
            print(f"STDOUT parcial:\n{exc.stdout}")
        if exc.stderr:
            print(f"STDERR parcial:\n{exc.stderr}")
        return 1
    except OSError as exc:
        print(f"ERROR: No se pudo ejecutar el módulo: {exc}")
        return 1

    show_process_result("EJECUCIÓN", execution_result)

    if execution_result.returncode != 0:
        print("ERROR: El módulo ARM64 devolvió un código distinto de cero.")
        return 1

    output_text = execution_result.stdout.strip()

    if result_file.exists():
        current_mtime = result_file.stat().st_mtime_ns
        file_output = result_file.read_text(
            encoding="utf-8", errors="replace"
        ).strip()

        print(f"\nArchivo de resultado: {result_file}")
        print(file_output or "(vacío)")

        if previous_mtime is None or current_mtime != previous_mtime:
            output_text = output_text or file_output
        else:
            print("ADVERTENCIA: El archivo existe, pero su fecha no cambió.")

    if not output_text:
        print("ERROR: No se recibió salida nueva por stdout ni por archivo.")
        return 1

    print("\nOK: Python compiló y ejecutó el módulo ARM64 correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
