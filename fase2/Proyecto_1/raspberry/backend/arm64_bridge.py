#!/usr/bin/env python3
"""Puente seguro entre Python y los módulos ARM64 del invernadero."""

from __future__ import annotations

import os
import platform
import re
import selectors
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Sequence


BACKEND_DIR = Path(__file__).resolve().parent
RASPBERRY_DIR = BACKEND_DIR.parent
ARM64_DIR = RASPBERRY_DIR / "arm64"
BUILD_DIR = ARM64_DIR / "build"
MAKEFILE = ARM64_DIR / "Makefile"

FASE1_MODULES = {
    1: {
        "module_name": "modulo_1_media",
        "result_file": "resultados_arm64/resultado_media.txt",
    },
    2: {
        "module_name": "modulo_2_varianza",
        "result_file": "resultados_arm64/resultado_varianza.txt",
    },
    3: {
        "module_name": "modulo_3_anomalias",
        "result_file": "resultados_arm64/resultado_anomalias.txt",
    },
    4: {
        "module_name": "modulo_4_prediccion",
        "result_file": "resultados_arm64/resultado_prediccion.txt",
    },
    5: {
        "module_name": "modulo_5_tendencia",
        "result_file": "resultados_arm64/resultado_tendencia.txt",
    },
}

FASE1_COLUMN_MAP = {
    2: "TEMP",
    3: "HUM_AIRE",
    4: "SOIL1",
    5: "SOIL2",
    6: "LUZ",
    7: "GAS",
}

FASE2_MODULES = {
    1: {
        "module_name": "modulo_1_rmse",
        "requires_ideal": True,
        "requires_k": False,
    },
    2: {
        "module_name": "modulo_2_regresion",
        "requires_ideal": False,
        "requires_k": False,
    },
    3: {
        "module_name": "modulo_3_prediccion_futura",
        "requires_ideal": False,
        "requires_k": True,
    },
    4: {
        "module_name": "modulo_4_integral_error",
        "requires_ideal": True,
        "requires_k": False,
    },
    5: {
        "module_name": "modulo_5_derivada_local",
        "requires_ideal": False,
        "requires_k": False,
    },
}

FASE2_MODULE_NAME_TO_NUMBER = {
    config["module_name"]: number
    for number, config in FASE2_MODULES.items()
}

KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_MOTOR_VIVO: subprocess.Popen[Any] | None = None
_MOTOR_VIVO_COMMAND: list[str] | None = None
_MOTOR_VIVO_LOCK = threading.RLock()


def parse_key_value_output(output_text: str) -> dict[str, str]:
    """Convierte líneas KEY=VALUE en un diccionario de cadenas."""
    parsed: dict[str, str] = {}

    if not output_text:
        return parsed

    for raw_line in str(output_text).splitlines():
        line = raw_line.strip()

        if not line or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if KEY_PATTERN.fullmatch(key):
            parsed[key] = value

    return parsed


def _text_from_timeout_value(value: Any) -> str:
    """Normaliza stdout/stderr provenientes de TimeoutExpired."""
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return str(value)


def run_command(
    command: Sequence[str | Path],
    cwd: str | Path,
    timeout: int | float,
    input_text: str | None = None,
) -> dict[str, Any]:
    """Ejecuta un comando y devuelve siempre un resultado estructurado."""
    normalized_command = [str(part) for part in command]
    normalized_cwd = Path(cwd).resolve()

    result: dict[str, Any] = {
        "ok": False,
        "status": "ERROR",
        "command": normalized_command,
        "cwd": str(normalized_cwd),
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "timeout": timeout,
        "timed_out": False,
    }

    try:
        completed = subprocess.run(
            normalized_command,
            cwd=str(normalized_cwd),
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        result.update(
            {
                "ok": completed.returncode == 0,
                "status": "OK" if completed.returncode == 0 else "ERROR",
                "returncode": completed.returncode,
                "stdout": completed.stdout or "",
                "stderr": completed.stderr or "",
            }
        )

        if completed.returncode != 0:
            detail = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"Command returned exit code {completed.returncode}"
            )
            result.update(
                {
                    "error": "EXECUTION_FAILED",
                    "detail": detail,
                }
            )

        return result

    except subprocess.TimeoutExpired as exc:
        result.update(
            {
                "error": "TIMEOUT",
                "detail": f"Command exceeded timeout of {timeout} seconds",
                "stdout": _text_from_timeout_value(exc.stdout),
                "stderr": _text_from_timeout_value(exc.stderr),
                "timed_out": True,
            }
        )
        return result

    except FileNotFoundError as exc:
        result.update(
            {
                "error": "COMMAND_NOT_FOUND",
                "detail": str(exc),
            }
        )
        return result

    except PermissionError as exc:
        result.update(
            {
                "error": "PERMISSION_DENIED",
                "detail": str(exc),
            }
        )
        return result

    except OSError as exc:
        result.update(
            {
                "error": "OS_ERROR",
                "detail": str(exc),
            }
        )
        return result

    except Exception as exc:
        result.update(
            {
                "error": "UNEXPECTED_ERROR",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )
        return result


def find_binary(module_name: str) -> Path | None:
    """Busca un binario primero en build/ y después en la raíz ARM64."""
    if not module_name or Path(module_name).name != module_name:
        return None

    candidates = (
        BUILD_DIR / module_name,
        ARM64_DIR / module_name,
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


def ensure_compiled(module_name: str) -> dict[str, Any]:
    """Compila los módulos con make all solamente si falta el solicitado."""
    existing_binary = find_binary(module_name)

    if existing_binary is not None:
        return {
            "ok": True,
            "status": "OK",
            "compiled": False,
            "module": module_name,
            "binary": str(existing_binary),
            "detail": "Binary already exists",
        }

    if not ARM64_DIR.is_dir():
        return {
            "ok": False,
            "status": "ERROR",
            "error": "ARM64_DIRECTORY_NOT_FOUND",
            "detail": f"ARM64 directory does not exist: {ARM64_DIR}",
            "module": module_name,
        }

    if not MAKEFILE.is_file():
        return {
            "ok": False,
            "status": "ERROR",
            "error": "MAKEFILE_NOT_FOUND",
            "detail": f"Makefile does not exist: {MAKEFILE}",
            "module": module_name,
        }

    if shutil.which("make") is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "MAKE_NOT_FOUND",
            "detail": "The make command is not available",
            "module": module_name,
        }

    make_result = run_command(
        ["make", "all"],
        cwd=ARM64_DIR,
        timeout=60,
    )

    found_binaries = [
        str(path)
        for path in sorted(
            {
                candidate.resolve()
                for directory in (BUILD_DIR, ARM64_DIR)
                if directory.is_dir()
                for candidate in directory.glob("modulo_*")
                if candidate.is_file()
                and candidate.suffix == ""
                and os.access(candidate, os.X_OK)
            },
            key=lambda path: str(path),
        )
    ]

    if not make_result["ok"]:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "COMPILATION_FAILED",
            "detail": make_result.get("detail", "make all failed"),
            "module": module_name,
            "compiled": False,
            "found_binaries": found_binaries,
            "make": make_result,
        }

    compiled_binary = find_binary(module_name)

    if compiled_binary is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "BINARY_NOT_FOUND",
            "detail": (
                f"make all completed but the binary was not found: {module_name}"
            ),
            "module": module_name,
            "compiled": True,
            "found_binaries": found_binaries,
            "make": make_result,
        }

    return {
        "ok": True,
        "status": "OK",
        "compiled": True,
        "module": module_name,
        "binary": str(compiled_binary),
        "found_binaries": found_binaries,
        "make": make_result,
    }


def _execution_prefix() -> dict[str, Any]:
    """Determina si la ejecución será nativa o mediante QEMU."""
    architecture = platform.machine().lower()

    if architecture in {"aarch64", "arm64"}:
        return {
            "ok": True,
            "status": "OK",
            "architecture": architecture,
            "execution_mode": "native",
            "prefix": [],
        }

    if architecture in {"x86_64", "amd64"}:
        qemu = shutil.which("qemu-aarch64")

        if qemu is None:
            return {
                "ok": False,
                "status": "ERROR",
                "error": "QEMU_NOT_FOUND",
                "detail": "The system is x86_64 and qemu-aarch64 is not available",
                "architecture": architecture,
            }

        return {
            "ok": True,
            "status": "OK",
            "architecture": architecture,
            "execution_mode": "qemu-aarch64",
            "prefix": [qemu],
        }

    return {
        "ok": False,
        "status": "ERROR",
        "error": "UNSUPPORTED_ARCHITECTURE",
        "detail": f"Unsupported host architecture: {architecture}",
        "architecture": architecture,
    }


def _resolve_result_file(result_file: str | Path | None) -> Path | None:
    if result_file is None:
        return None

    path = Path(result_file)

    if not path.is_absolute():
        path = ARM64_DIR / path

    return path.resolve()


def run_arm64_module(
    module_name: str,
    args: Sequence[Any] | None = None,
    input_text: str | None = None,
    timeout: int | float = 10,
    result_file: str | Path | None = None,
) -> dict[str, Any]:
    """Ejecuta un binario ARM64 y obtiene salida de stdout o archivo."""
    normalized_args = [str(arg) for arg in (args or [])]

    response: dict[str, Any] = {
        "ok": False,
        "status": "ERROR",
        "module": module_name,
        "args": normalized_args,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "result_file": None,
        "output_text": "",
        "parsed": {},
        "timeout": timeout,
        "timed_out": False,
    }

    if not module_name or Path(module_name).name != module_name:
        response.update(
            {
                "error": "INVALID_MODULE_NAME",
                "detail": f"Invalid module name: {module_name!r}",
            }
        )
        return response

    compilation = ensure_compiled(module_name)
    response["compilation"] = compilation

    if not compilation["ok"]:
        response.update(
            {
                "error": compilation.get("error", "COMPILATION_FAILED"),
                "detail": compilation.get(
                    "detail", "The ARM64 binary could not be prepared"
                ),
            }
        )
        return response

    binary = find_binary(module_name)

    if binary is None:
        response.update(
            {
                "error": "BINARY_NOT_FOUND",
                "detail": f"Binary not found: {module_name}",
            }
        )
        return response

    execution = _execution_prefix()
    response["architecture"] = execution.get("architecture")
    response["execution_mode"] = execution.get("execution_mode")

    if not execution["ok"]:
        response.update(
            {
                "error": execution.get("error", "EXECUTION_NOT_AVAILABLE"),
                "detail": execution.get(
                    "detail", "ARM64 execution is not available"
                ),
            }
        )
        return response

    resolved_result_file = _resolve_result_file(result_file)
    previous_signature: tuple[int, int] | None = None

    if resolved_result_file is not None:
        response["result_file"] = str(resolved_result_file)
        resolved_result_file.parent.mkdir(parents=True, exist_ok=True)

        if resolved_result_file.exists():
            previous_stat = resolved_result_file.stat()
            previous_signature = (
                previous_stat.st_mtime_ns,
                previous_stat.st_size,
            )

    command = [
        *execution["prefix"],
        str(binary),
        *normalized_args,
    ]

    command_result = run_command(
        command,
        cwd=ARM64_DIR,
        timeout=timeout,
        input_text=input_text,
    )

    response.update(
        {
            "returncode": command_result.get("returncode"),
            "stdout": command_result.get("stdout", ""),
            "stderr": command_result.get("stderr", ""),
            "timed_out": command_result.get("timed_out", False),
            "command": command_result.get("command", command),
            "binary": str(binary),
        }
    )

    if not command_result["ok"]:
        response.update(
            {
                "error": command_result.get("error", "EXECUTION_FAILED"),
                "detail": command_result.get("detail", "The ARM64 module failed"),
            }
        )
        return response

    stdout_text = command_result.get("stdout", "").strip()
    file_text = ""
    result_file_updated = False

    if resolved_result_file is not None and resolved_result_file.is_file():
        current_stat = resolved_result_file.stat()
        current_signature = (
            current_stat.st_mtime_ns,
            current_stat.st_size,
        )

        result_file_updated = (
            previous_signature is None or current_signature != previous_signature
        )

        if result_file_updated:
            try:
                file_text = resolved_result_file.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).strip()
            except OSError as exc:
                response.update(
                    {
                        "error": "RESULT_FILE_READ_FAILED",
                        "detail": str(exc),
                    }
                )
                return response

    output_text = file_text or stdout_text
    parsed = parse_key_value_output(output_text)

    response.update(
        {
            "result_file_updated": result_file_updated,
            "output_text": output_text,
            "parsed": parsed,
        }
    )

    if not output_text:
        response.update(
            {
                "error": "OUTPUT_NOT_FOUND",
                "detail": (
                    "The module returned exit code 0 but produced no new "
                    "stdout or result file output"
                ),
            }
        )
        return response

    response.update(
        {
            "ok": True,
            "status": "OK",
        }
    )
    return response


def run_fase1_module(
    module_number: int,
    column: int | str = 2,
    file_path: str | Path = "lecturas.csv",
    start_line: int | str = 1,
    end_line: int | str = 30,
) -> dict[str, Any]:
    """Ejecuta uno de los cinco módulos migrados con contrato de Fase 2."""
    try:
        normalized_module_number = int(module_number)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_MODULE",
            "detail": f"Invalid Phase 1 module number: {module_number!r}",
        }

    module_config = FASE1_MODULES.get(normalized_module_number)

    if module_config is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_MODULE",
            "detail": "Phase 1 module number must be between 1 and 5",
            "module_number": normalized_module_number,
        }

    if isinstance(start_line, bool) or isinstance(end_line, bool):
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
            "module_number": normalized_module_number,
        }

    try:
        normalized_start_line = int(start_line)
        normalized_end_line = int(end_line)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
            "module_number": normalized_module_number,
        }

    if normalized_start_line < 1 or normalized_end_line < normalized_start_line:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "Invalid line range",
            "module_number": normalized_module_number,
            "start_line": normalized_start_line,
            "end_line": normalized_end_line,
        }

    logical_column = _normalize_fase1_column(column)
    if logical_column is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_COLUMN",
            "detail": "column must be 2..7 or TEMP, HUM_AIRE, SOIL1, SOIL2, LUZ, GAS",
            "module_number": normalized_module_number,
        }

    normalized_file_path = str(file_path or "lecturas.csv")

    result = run_arm64_module(
        module_name=module_config["module_name"],
        args=[
            normalized_file_path,
            str(normalized_start_line),
            str(normalized_end_line),
            logical_column,
        ],
        timeout=10,
        result_file=module_config["result_file"],
    )

    result["module_number"] = normalized_module_number
    result["file_path"] = normalized_file_path
    result["start_line"] = normalized_start_line
    result["end_line"] = normalized_end_line
    result["column"] = logical_column
    return result


def _normalize_fase1_column(column: int | str) -> str | None:
    if isinstance(column, bool):
        return None

    if isinstance(column, str):
        stripped = column.strip().upper()
        if stripped.isdigit():
            return FASE1_COLUMN_MAP.get(int(stripped))
        if stripped in set(FASE1_COLUMN_MAP.values()):
            return stripped
        return None

    try:
        return FASE1_COLUMN_MAP.get(int(column))
    except (TypeError, ValueError):
        return None


def run_fase2_module(
    module_number: int | None = None,
    module_name: str | None = None,
    file_path: str | Path = "lecturas.csv",
    start_line: int | str = 1,
    end_line: int | str = 30,
    column: int | str = "TEMP",
    ideal: int | str = 25,
    k: int | str = 5,
) -> dict[str, Any]:
    """Ejecuta uno de los módulos avanzados de Fase 2."""
    normalized_module_number: int | None = None

    if module_number is not None:
        try:
            normalized_module_number = int(module_number)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "status": "ERROR",
                "error": "INVALID_MODULE",
                "detail": f"Invalid Phase 2 module number: {module_number!r}",
            }

    if normalized_module_number is None and module_name:
        normalized_name = str(module_name).strip()
        normalized_module_number = FASE2_MODULE_NAME_TO_NUMBER.get(normalized_name)

    module_config = FASE2_MODULES.get(normalized_module_number)

    if module_config is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_MODULE",
            "detail": "Phase 2 module must be 1..5 or an allowed module_name",
            "module_number": normalized_module_number,
            "module_name": module_name,
        }

    if isinstance(start_line, bool) or isinstance(end_line, bool):
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
            "module_number": normalized_module_number,
        }

    try:
        normalized_start_line = int(start_line)
        normalized_end_line = int(end_line)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "start_line and end_line must be integers",
            "module_number": normalized_module_number,
        }

    if normalized_start_line < 1 or normalized_end_line < normalized_start_line:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_RANGE",
            "detail": "Invalid line range",
            "module_number": normalized_module_number,
            "start_line": normalized_start_line,
            "end_line": normalized_end_line,
        }

    logical_column = _normalize_fase1_column(column)
    if logical_column is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_COLUMN",
            "detail": "column must be 2..7 or TEMP, HUM_AIRE, SOIL1, SOIL2, LUZ, GAS",
            "module_number": normalized_module_number,
        }

    args = [
        str(file_path or "lecturas.csv"),
        str(normalized_start_line),
        str(normalized_end_line),
        logical_column,
    ]

    if module_config["requires_ideal"]:
        args.append(str(ideal))

    if module_config["requires_k"]:
        args.append(str(k))

    result = run_arm64_module(
        module_name=module_config["module_name"],
        args=args,
        timeout=15,
        result_file=None,
    )

    output_text = (
        result.get("output_text", "").strip()
        or result.get("stdout", "").strip()
    )
    parsed = parse_key_value_output(output_text)

    result.update(
        {
            "phase": "fase2",
            "module_number": normalized_module_number,
            "module_name": module_config["module_name"],
            "file_path": str(file_path or "lecturas.csv"),
            "start_line": normalized_start_line,
            "end_line": normalized_end_line,
            "column": logical_column,
            "ideal": ideal,
            "k": k,
            "output_text": output_text,
            "parsed": parsed,
        }
    )

    parsed_status = parsed.get("STATUS")
    if parsed_status == "ERROR":
        result.update(
            {
                "ok": False,
                "status": "ERROR",
                "error": parsed.get("ERROR", result.get("error", "ARM64_ERROR")),
                "detail": parsed.get("DETAIL", result.get("detail", "ARM64 failed")),
            }
        )
        return result

    if parsed_status == "OK" and result.get("returncode") == 0:
        result.update({"ok": True, "status": "OK"})
        result.pop("error", None)
        result.pop("detail", None)

    return result


def run_historical_analysis(
    file_path: str,
    start_line: int,
    end_line: int,
    column: str,
    module_name: str,
    ideal: int | str = 25,
    k: int | str = 10,
    timeout: int | float = 15,
) -> dict[str, Any]:
    """Ejecuta el analizador histórico ARM64 completo sin cálculos Python."""
    if module_name != "historical_analyzer":
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_MODULE",
            "detail": "Historical module must be historical_analyzer",
            "module": module_name,
        }

    logical_column = _normalize_fase1_column(column)
    if logical_column is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_COLUMN",
            "detail": "column must be 2..7 or TEMP, HUM_AIRE, SOIL1, SOIL2, LUZ, GAS",
            "column": column,
        }

    result = run_arm64_module(
        module_name=module_name,
        args=[
            str(file_path),
            str(start_line),
            str(end_line),
            str(logical_column),
            str(ideal),
            str(k),
        ],
        timeout=timeout,
        result_file=None,
    )

    output_text = (
        result.get("output_text", "").strip()
        or result.get("stdout", "").strip()
    )
    parsed = parse_key_value_output(output_text)

    result.update(
        {
            "analysis_type": "historical_arm64",
            "file_path": str(file_path),
            "start_line": start_line,
            "end_line": end_line,
            "column": logical_column,
            "ideal": ideal,
            "k": k,
            "output_text": output_text,
            "raw_output": output_text,
            "parsed": parsed,
        }
    )

    parsed_status = parsed.get("STATUS")
    if parsed_status == "ERROR":
        result.update(
            {
                "ok": False,
                "status": "ERROR",
                "error": parsed.get(
                    "ERROR",
                    result.get("error", "HISTORICAL_ANALYSIS_FAILED"),
                ),
                "detail": parsed.get(
                    "DETAIL",
                    result.get("detail", "Historical analyzer failed"),
                ),
            }
        )
        return result

    if parsed_status == "OK" and result.get("returncode") == 0:
        result.update({"ok": True, "status": "OK"})
        result.pop("error", None)
        result.pop("detail", None)
        return result

    if not result.get("ok"):
        return result

    result.update(
        {
            "ok": False,
            "status": "ERROR",
            "error": "INVALID_OUTPUT",
            "detail": "Historical analyzer returned an invalid response",
        }
    )
    return result

def run_live_engine(
    reading_dict: dict,
    timeout: int | float = 10,
) -> dict[str, Any]:
    """Ejecuta el motor de decisiones en vivo de Fase 2."""
    try:
        input_line = _build_live_engine_input(reading_dict)
    except (TypeError, ValueError) as exc:
        return _live_engine_response(
            status="ERROR",
            error="INVALID_INPUT",
            detail=str(exc),
            reading=reading_dict,
        )

    result = enviar_lectura_motor(input_line, timeout=timeout)
    output_text = (result.get("stdout") or "").strip()
    parsed = parse_key_value_output(output_text)
    status = parsed.get("STATUS", result.get("status", "ERROR"))

    response = _live_engine_response(
        status=status,
        action=parsed.get("ACTION"),
        target=parsed.get("TARGET"),
        risk=parsed.get("RISK"),
        reason=parsed.get("REASON"),
        value=parsed.get("VALUE"),
        indicator=parsed.get("INDICATOR"),
        error=parsed.get("ERROR") or result.get("error"),
        detail=parsed.get("DETAIL") or result.get("detail"),
        reading=reading_dict,
        input_line=input_line,
        raw_output=output_text,
        raw_result=result,
    )

    response["ok"] = bool(result.get("ok")) and status == "OK"
    return response


def iniciar_motor_vivo() -> dict[str, Any]:
    # esto inicia el proceso persistente del motor vivo
    global _MOTOR_VIVO, _MOTOR_VIVO_COMMAND

    with _MOTOR_VIVO_LOCK:
        if motor_vivo_activo():
            assert _MOTOR_VIVO is not None
            return {
                "ok": True,
                "status": "OK",
                "pid": _MOTOR_VIVO.pid,
                "command": _MOTOR_VIVO_COMMAND or [],
                "reused": True,
            }

        compile_result = _ensure_live_engine_compiled()
        if not compile_result.get("ok"):
            return {
                "ok": False,
                "status": "ERROR",
                "error": compile_result.get("error", "COMPILE_ERROR"),
                "detail": compile_result.get("detail", "Could not compile live_engine"),
                "raw_result": compile_result,
            }

        binary_path = find_binary("live_engine")
        if binary_path is None:
            return {
                "ok": False,
                "status": "ERROR",
                "error": "BINARY_NOT_FOUND",
                "detail": "live_engine binary was not found",
            }

        command = _live_engine_command(binary_path)

        try:
            _MOTOR_VIVO = subprocess.Popen(
                command,
                cwd=str(ARM64_DIR),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
            _MOTOR_VIVO_COMMAND = command
        except FileNotFoundError as exc:
            _MOTOR_VIVO = None
            return {
                "ok": False,
                "status": "ERROR",
                "error": "COMMAND_NOT_FOUND",
                "detail": str(exc),
                "command": command,
            }
        except OSError as exc:
            _MOTOR_VIVO = None
            return {
                "ok": False,
                "status": "ERROR",
                "error": "OS_ERROR",
                "detail": str(exc),
                "command": command,
            }

        return {
            "ok": True,
            "status": "OK",
            "pid": _MOTOR_VIVO.pid,
            "command": command,
            "reused": False,
        }


def motor_vivo_activo() -> bool:
    # esto verifica si el motor sigue vivo
    process = _MOTOR_VIVO
    return (
        process is not None
        and process.poll() is None
        and process.stdin is not None
        and process.stdout is not None
    )


def reiniciar_motor_vivo() -> dict[str, Any]:
    # esto reinicia el proceso sin guardar historial en python
    with _MOTOR_VIVO_LOCK:
        cerrar_motor_vivo()
        return iniciar_motor_vivo()


def enviar_lectura_motor(
    input_line: str,
    timeout: int | float = 10,
) -> dict[str, Any]:
    # esto envia una lectura al proceso persistente
    with _MOTOR_VIVO_LOCK:
        last_response: dict[str, Any] | None = None

        for attempt in range(2):
            start_result = iniciar_motor_vivo()
            if not start_result.get("ok"):
                return start_result

            process = _MOTOR_VIVO
            if process is None or process.stdin is None:
                return {
                    "ok": False,
                    "status": "ERROR",
                    "error": "PROCESS_NOT_AVAILABLE",
                    "detail": "live_engine process is not available",
                    "input_line": input_line,
                }

            try:
                process.stdin.write(f"{input_line}\n".encode("utf-8"))
                process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                restart_result = reiniciar_motor_vivo()
                last_response = {
                    "ok": False,
                    "status": "ERROR",
                    "error": "PROCESS_RESTARTED",
                    "detail": str(exc),
                    "input_line": input_line,
                    "restart": restart_result,
                    "pid": process.pid,
                    "command": _MOTOR_VIVO_COMMAND or [],
                }
                if attempt == 0:
                    continue
                return last_response

            response = leer_respuesta_motor(timeout=timeout)
            response["input_line"] = input_line
            response["pid"] = process.pid
            response["command"] = _MOTOR_VIVO_COMMAND or []

            if response.get("error") == "PROCESS_EXITED" and attempt == 0:
                response["restart"] = reiniciar_motor_vivo()
                last_response = response
                continue

            return response

        assert last_response is not None
        return last_response


def leer_respuesta_motor(timeout: int | float = 10) -> dict[str, Any]:
    # esto lee hasta encontrar status del motor
    process = _MOTOR_VIVO
    if process is None or process.stdout is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "PROCESS_NOT_AVAILABLE",
            "detail": "live_engine stdout is not available",
            "stdout": "",
        }

    chunks: list[bytes] = []
    deadline = time.monotonic() + float(timeout)
    selector = selectors.DefaultSelector()

    try:
        stdout_fd = process.stdout.fileno()
        selector.register(stdout_fd, selectors.EVENT_READ)

        while True:
            if process.poll() is not None:
                stderr_text = ""
                if process.stderr is not None:
                    stderr_text = (process.stderr.read() or b"").decode(
                        "utf-8",
                        errors="replace",
                    )
                return {
                    "ok": False,
                    "status": "ERROR",
                    "error": "PROCESS_EXITED",
                    "detail": f"live_engine exited with code {process.returncode}",
                    "stdout": b"".join(chunks).decode("utf-8", errors="replace"),
                    "stderr": stderr_text,
                    "returncode": process.returncode,
                }

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                restart_result = reiniciar_motor_vivo()
                return {
                    "ok": False,
                    "status": "ERROR",
                    "error": "TIMEOUT",
                    "detail": f"live_engine exceeded timeout of {timeout} seconds",
                    "stdout": b"".join(chunks).decode("utf-8", errors="replace"),
                    "timed_out": True,
                    "restart": restart_result,
                }

            events = selector.select(timeout=remaining)
            if not events:
                restart_result = reiniciar_motor_vivo()
                return {
                    "ok": False,
                    "status": "ERROR",
                    "error": "TIMEOUT",
                    "detail": f"live_engine exceeded timeout of {timeout} seconds",
                    "stdout": b"".join(chunks).decode("utf-8", errors="replace"),
                    "timed_out": True,
                    "restart": restart_result,
                }

            chunk = os.read(stdout_fd, 4096)
            if not chunk:
                continue

            chunks.append(chunk)
            output_text = b"".join(chunks).decode("utf-8", errors="replace")
            parsed = parse_key_value_output(output_text)
            status = parsed.get("STATUS")

            if status in {"OK", "ERROR"}:
                return {
                    "ok": status == "OK",
                    "status": status,
                    "stdout": output_text,
                    "stderr": "",
                    "returncode": process.poll(),
                    "timed_out": False,
                }
    finally:
        selector.close()


def cerrar_motor_vivo() -> None:
    # esto cierra el proceso persistente del motor vivo
    global _MOTOR_VIVO, _MOTOR_VIVO_COMMAND

    process = _MOTOR_VIVO
    _MOTOR_VIVO = None
    _MOTOR_VIVO_COMMAND = None

    if process is None:
        return

    try:
        if process.stdin is not None and process.poll() is None:
            process.stdin.write(b"n\n")
            process.stdin.flush()
    except (BrokenPipeError, OSError):
        pass

    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def _live_engine_response(
    *,
    status: str,
    action: str | None = None,
    target: str | None = None,
    risk: str | None = None,
    reason: str | None = None,
    value: str | None = None,
    indicator: str | None = None,
    error: str | None = None,
    detail: str | None = None,
    reading: dict | None = None,
    input_line: str | None = None,
    raw_output: str | None = None,
    raw_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # esto mantiene estable el contrato del motor vivo
    response: dict[str, Any] = {
        "ok": status == "OK",
        "status": status,
        "action": action,
        "target": target,
        "risk": risk,
        "reason": reason,
        "value": value,
        "indicator": indicator,
        "error": error,
        "detail": detail,
    }

    if reading is not None:
        response["reading"] = dict(reading)

    if input_line is not None:
        response["input_line"] = input_line

    if raw_output is not None:
        response["raw_output"] = raw_output

    if raw_result is not None:
        response["raw_result"] = raw_result

    return response


def _build_live_engine_input(reading_dict: dict) -> str:
    # esto construye la linea que consume arm64
    values = [
        _live_int(reading_dict, "temp", "TEMP"),
        _live_int(reading_dict, "hum", "HUM_AIRE"),
        _live_int(reading_dict, "soil1", "SOIL1", aliases=("val_s1",)),
        _live_int(reading_dict, "soil2", "SOIL2", aliases=("val_s2",)),
        _live_int(reading_dict, "luz", "LUZ", aliases=("val_luz",)),
        _live_int(reading_dict, "gas", "GAS", aliases=("val_gas",)),
        _live_mode(reading_dict),
    ]
    return ",".join(str(value) for value in values)


def _live_int(
    reading_dict: dict,
    key: str,
    label: str,
    aliases: Sequence[str] = (),
) -> int:
    # esto normaliza enteros para stdin
    value = reading_dict.get(key)

    for alias in aliases:
        if value is not None:
            break
        value = reading_dict.get(alias)

    if value is None or value == "":
        raise ValueError(f"{label} is required")

    try:
        number = int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc

    if number < 0:
        raise ValueError(f"{label} must be positive")

    return number


def _live_mode(reading_dict: dict) -> int:
    # esto convierte modo a valor numerico
    raw_mode = reading_dict.get("modo", reading_dict.get("mode", 1))

    if isinstance(raw_mode, str):
        normalized = raw_mode.strip().upper()
        if normalized in {"AUTOMATICO", "AUTO", "1", "ON"}:
            return 1
        if normalized in {"MANUAL", "0", "OFF"}:
            return 0

    return 1 if _live_int({"modo": raw_mode}, "modo", "MODO") != 0 else 0


def _live_engine_command(binary_path: Path) -> list[str]:
    # esto permite ejecutar arm64 en pc con qemu
    if platform.machine().lower() in {"aarch64", "arm64"}:
        return [str(binary_path)]

    qemu_path = shutil.which("qemu-aarch64")
    if qemu_path:
        return [qemu_path, str(binary_path)]

    return [str(binary_path)]


def _ensure_live_engine_compiled() -> dict[str, Any]:
    # esto compila solo el motor vivo si hace falta
    existing_binary = find_binary("live_engine")

    if existing_binary is not None:
        return {
            "ok": True,
            "status": "OK",
            "compiled": False,
            "module": "live_engine",
            "binary": str(existing_binary),
        }

    if not MAKEFILE.is_file():
        return {
            "ok": False,
            "status": "ERROR",
            "error": "MAKEFILE_NOT_FOUND",
            "detail": f"Makefile does not exist: {MAKEFILE}",
            "module": "live_engine",
        }

    if shutil.which("make") is None:
        return {
            "ok": False,
            "status": "ERROR",
            "error": "MAKE_NOT_FOUND",
            "detail": "The make command is not available",
            "module": "live_engine",
        }

    make_result = run_command(
        ["make", "live_engine"],
        cwd=ARM64_DIR,
        timeout=60,
    )

    binary_path = find_binary("live_engine")
    if make_result.get("ok") and binary_path is not None:
        make_result.update(
            {
                "compiled": True,
                "module": "live_engine",
                "binary": str(binary_path),
            }
        )
        return make_result

    make_result.update(
        {
            "ok": False,
            "status": "ERROR",
            "error": make_result.get("error", "COMPILE_ERROR"),
            "detail": make_result.get("detail", "Could not compile live_engine"),
            "module": "live_engine",
        }
    )
    return make_result
