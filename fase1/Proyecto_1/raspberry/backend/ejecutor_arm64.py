"""
ejecutor_arm64.py
Ejecuta binarios ARM64 nativos ubicados en ../arm64/build.

Este archivo NO usa qemu-aarch64 porque está pensado para correr
nativamente en Raspberry Pi con arquitectura ARM64.
"""

from pathlib import Path
import subprocess
from typing import Optional


# backend/ejecutor_arm64.py -> raspberry/arm64
ARM64_DIR = Path(__file__).resolve().parent.parent / "arm64"
CSV_ENTRADA = ARM64_DIR / "lecturas.csv"

MODULOS = {
    1: "modulo_1_media",
    2: "modulo_2_varianza",
    3: "modulo_3_anomalias",
    4: "modulo_4_prediccion",
    5: "modulo_5_tendencia",
}


def ejecutar_modulo_arm64(
    numero_modulo: int,
    columna: int,
    csv_path: Optional[Path] = None,
    timeout: int = 10,
) -> str:
    """
    Ejecuta un módulo ARM64 nativo.

    Parámetros:
    - numero_modulo: número del módulo, de 1 a 5.
    - columna: columna del CSV que analizará el módulo. Se usan columnas 2 a 7.
    - csv_path: archivo CSV de entrada. Por defecto: ../arm64/entrada_sensores.csv.
    - timeout: tiempo máximo de ejecución en segundos.

    Nota:
    Los binarios se ejecutan con cwd=ARM64_DIR para que puedan abrir
    entrada_sensores.csv usando una ruta relativa simple.
    """

    if numero_modulo not in MODULOS:
        raise ValueError("Módulo inválido. Usa un número entre 1 y 5.")

    if columna < 2 or columna > 7:
        raise ValueError("Columna inválida. Usa columnas de sensores: 2 a 7.")

    entrada = Path(csv_path) if csv_path else CSV_ENTRADA
    binario = ARM64_DIR / "build" / MODULOS[numero_modulo]

    if not binario.exists():
        raise FileNotFoundError(f"No existe el binario ARM64: {binario}")

    if not entrada.exists():
        raise FileNotFoundError(f"No existe el CSV de entrada: {entrada}")

    # Se conserva el contrato base: el binario recibe la columna.
    # El CSV queda disponible en cwd=ARM64_DIR como entrada_sensores.csv.
    resultado = subprocess.run(
        [str(binario), str(columna)],
        cwd=str(ARM64_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )

    if resultado.returncode != 0:
        error = resultado.stderr.strip() or resultado.stdout.strip() or "Error ejecutando módulo ARM64"
        raise RuntimeError(error)

    return resultado.stdout.strip()
