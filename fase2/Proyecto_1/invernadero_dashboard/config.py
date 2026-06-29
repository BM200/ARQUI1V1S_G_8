import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env", override=False)

class Config:
    MQTT_BROKER = "broker.emqx.io"
    MQTT_PORT   = 1883
    MQTT_USER   = ""
    MQTT_PASSWORD = ""

    MONGO_URI     = os.getenv("MONGO_URI", "")
    MONGO_DB      = os.getenv("MONGO_DB_NAME", "invernadero_g8")

    _BASE = "invernadero/G8/P1"   # ← variable privada de clase

    TOPICS = {
        "temperatura":        f"invernadero/G8/P1/sensores/temperatura",
        "humedad_ambiente":   f"invernadero/G8/P1/sensores/humedad_ambiente",
        "humedad_suelo_area1": f"invernadero/G8/P1/sensores/humedad_suelo_area1",
        "humedad_suelo_area2": f"invernadero/G8/P1/sensores/humedad_suelo_area2",
        "luz":                f"invernadero/G8/P1/sensores/luz",
        "gas":                f"invernadero/G8/P1/sensores/gas",
        "riego":              f"invernadero/G8/P1/actuadores/riego",
        "riego_area1":        f"invernadero/G8/P1/actuadores/riego_area1",
        "riego_area2":        f"invernadero/G8/P1/actuadores/riego_area2",
        "ventilador":         f"invernadero/G8/P1/actuadores/ventilador",
        "luces":              f"invernadero/G8/P1/actuadores/luces",
        "alarma":             f"invernadero/G8/P1/actuadores/alarma",
        "estado_global":      f"invernadero/G8/P1/estado/global",
        "control_remoto":     f"invernadero/G8/P1/control/remoto",
        "control_manual":     f"invernadero/G8/P1/control/manual",
    }