#!/usr/bin/env python3
"""Prueba aislada de conexión, escritura y lectura en MongoDB."""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: Falta python-dotenv. Instala las dependencias del proyecto.")
    sys.exit(1)

try:
    from pymongo import MongoClient
except ImportError:
    print("ERROR: Falta pymongo. Instala las dependencias del proyecto.")
    sys.exit(1)


PROJECT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_DIR / ".env"


def main() -> int:
    print("=== PRUEBA MONGODB AISLADA ===")
    print(f"Archivo de configuración esperado: {ENV_FILE}")

    if not ENV_FILE.is_file():
        print("ERROR: Falta Proyecto_1/.env")
        print("Copia Proyecto_1/.env.example a Proyecto_1/.env y configura MONGO_URI.")
        return 2

    load_dotenv(ENV_FILE, override=False)

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    database_name = os.getenv("MONGO_DB_NAME", "invernadero_g8").strip()

    if not mongo_uri:
        print("ERROR: MONGO_URI está vacío o no está definido en Proyecto_1/.env")
        return 2

    if not database_name:
        print("ERROR: MONGO_DB_NAME está vacío.")
        return 2

    client = None
    test_id = str(uuid.uuid4())

    document = {
        "test_id": test_id,
        "timestamp": datetime.now(timezone.utc),
        "test_type": "mongodb_connection",
        "status": "created",
        "source": "Proyecto_1/tests/test_mongodb.py",
    }

    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )

        client.admin.command("ping")
        print("OK: Conexión y ping a MongoDB exitosos.")

        collection = client[database_name]["system_tests"]
        insert_result = collection.insert_one(document)

        print(f"OK: Documento insertado con _id={insert_result.inserted_id}")

        recovered = collection.find_one(
            {"test_id": test_id},
            {"_id": 0},
        )

        if recovered is None:
            print("ERROR: El documento fue insertado, pero no pudo leerse.")
            return 1

        if recovered.get("test_id") != test_id:
            print("ERROR: El documento recuperado no coincide con el insertado.")
            return 1

        print(f"OK: Documento leído desde {database_name}.system_tests")
        print(f"test_id={recovered['test_id']}")
        print("\nOK: Prueba MongoDB completada correctamente.")
        return 0

    except Exception as exc:
        print(f"ERROR: Falló la prueba MongoDB: {type(exc).__name__}: {exc}")
        return 1

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
