#!/usr/bin/env python3
from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ARM64_DIR = ROOT_DIR / "raspberry" / "arm64"
BINARY = ARM64_DIR / "build" / "live_engine"


def run_command(command, *, cwd=None, input_text=None, timeout=15):
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def compile_live_engine():
    print("Compilando live_engine...")
    result = run_command(["make", "live_engine"], cwd=ARM64_DIR)

    print("STDOUT make:")
    print(result.stdout)

    print("STDERR make:")
    print(result.stderr)

    if result.returncode != 0:
        raise AssertionError(f"make live_engine falló con código {result.returncode}")

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


def run_live_case(name: str, stdin_text: str, expected_texts: list[str]):
    command = get_runner()

    print(f"\nCaso: {name}")
    print("STDIN:")
    print(stdin_text)

    result = run_command(
        command,
        cwd=ARM64_DIR,
        input_text=stdin_text,
        timeout=10,
    )

    print("STDOUT live_engine:")
    print(result.stdout)

    print("STDERR live_engine:")
    print(result.stderr)

    if result.returncode != 0:
        raise AssertionError(
            f"live_engine terminó con código {result.returncode} en caso {name}"
        )

    for text in expected_texts:
        if text not in result.stdout:
            raise AssertionError(f"No se encontró en stdout para {name}: {text}")

    print(f"OK: {name}")


def main():
    compile_live_engine()

    run_live_case(
        name="entrada válida",
        stdin_text="10 20\nn\n",
        expected_texts=[
            "MODULE=LIVE_ENGINE",
            "STATUS=OK",
            "SUM=30",
        ],
    )

    run_live_case(
        name="entrada inválida",
        stdin_text="abc 20\nn\n",
        expected_texts=[
            "MODULE=LIVE_ENGINE",
            "STATUS=ERROR",
            "ERROR=INVALID_INPUT",
        ],
    )

    print("\nTEST LIVE_ENGINE: OK")


if __name__ == "__main__":
    main()
