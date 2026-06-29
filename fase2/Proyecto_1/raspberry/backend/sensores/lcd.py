import threading
import time
from datetime import datetime

try:
    from RPLCD.i2c import CharLCD
    LCD_DISPONIBLE = True
except ImportError:
    LCD_DISPONIBLE = False

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


if LCD_DISPONIBLE:
    try:
        lcd = CharLCD('PCF8574', 0x27)
        lcd.clear()
        time.sleep(0.5)
        print("[LCD] Conectado en 0x27")
    except OSError:
        LCD_DISPONIBLE = False
        print("[LCD] No se encontró en 0x27 — desactivado")


_secciones = {
    "temp":    ("Temperatura",  "Iniciando..."),
    "hum":     ("Humedad",      "Iniciando..."),
    "suelo1":  ("Suelo Area 1", "Iniciando..."),
    "suelo2":  ("Suelo Area 2", "Iniciando..."),
    "luz":     ("Luz",          "Iniciando..."),
    "gas":     ("Gas",          "Iniciando..."),
    "global":  ("Sistema",      "OK"),
}

_indice_actual  = 0
_timer_rotacion = None
_claves         = list(_secciones.keys())
_lock           = threading.Lock()

_ultima_linea1 = ""
_ultima_linea2 = ""

def _reiniciar_lcd():
    global lcd, LCD_DISPONIBLE
    if not LCD_DISPONIBLE:
        return
    try:
        lcd = CharLCD('PCF8574', 0x27)
        time.sleep(0.2)
    except Exception:
        LCD_DISPONIBLE = False

def _escribir(linea1: str, linea2: str = ""):
    """Escritura robusta — solo escribe si cambió, maneja ruido I2C."""
    global _ultima_linea1, _ultima_linea2

    # Truncar a 16 caracteres
    linea1 = linea1[:16]
    linea2 = linea2[:16]

    if linea1 == _ultima_linea1 and linea2 == _ultima_linea2:
        return

    if not LCD_DISPONIBLE:
        print(f"[LCD] {linea1} | {linea2}")
        return

    try:
        lcd.clear()
        lcd.write_string(linea1)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(linea2)
        _ultima_linea1 = linea1
        _ultima_linea2 = linea2
    except OSError:
        # Ruido en I2C — reiniciar igual que tu compañero
        print("[LCD] Ruido detectado, reiniciando...")
        time.sleep(0.2)
        _reiniciar_lcd()

def _mostrar_seccion(clave: str):
    with _lock:
        titulo, valor = _secciones.get(clave, ("???", "???"))
    _escribir(titulo, valor)


def _rotar():
    """Callback del Timer — avanza al siguiente mensaje."""
    global _indice_actual, _timer_rotacion

    _indice_actual = (_indice_actual + 1) % len(_claves)
    _mostrar_seccion(_claves[_indice_actual])

    # Autoprograma el próximo cambio — 3 segundos por sección
    _timer_rotacion = threading.Timer(3.0, _rotar)
    _timer_rotacion.daemon = True
    _timer_rotacion.start()


def actualizar_seccion(clave: str, valor: str):
    with _lock:
        if clave in _secciones:
            titulo = _secciones[clave][0]   # mantiene el título
            _secciones[clave] = (titulo, valor)

    # Si es emergencia, mostrar inmediatamente sin esperar la rotación
    if "EMERGENCIA" in valor or "ADVERTENCIA" in valor:
        mostrar_alerta_fija(
            _secciones[clave][0],
            valor
        )

def mostrar_alerta_fija(linea1: str, linea2: str):
    global _timer_rotacion
    if _timer_rotacion:
        _timer_rotacion.cancel()
        _timer_rotacion = None
    _escribir(linea1, linea2)
    print(f"[LCD] ALERTA FIJA: {linea1} | {linea2}")

def reanudar_rotacion():
    global _timer_rotacion
    if _timer_rotacion is None:
        _rotar()
    print("[LCD] Rotación reanudada")

def iniciar():
    if not LCD_DISPONIBLE:
        return
    _escribir("Invernadero G8", "Iniciando...")
    time.sleep(1)
    _rotar()
    print("[LCD] Rotación iniciada")

def detener():
    global _timer_rotacion
    if _timer_rotacion:
        _timer_rotacion.cancel()
        _timer_rotacion = None
    if LCD_DISPONIBLE:
        try:
            lcd.clear()
            lcd.backlight_enabled = False
        except Exception:
            pass
    print("[LCD] Detenido")