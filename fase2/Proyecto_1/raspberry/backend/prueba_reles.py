import time
from gpiozero import OutputDevice

# Define los pines GPIO reales que vas a usar (Ajusta los números según tus cables)
PIN_BOMBA = 17   # GPIO17 (Pin físico 11)
PIN_LUCES = 27   # GPIO27 (Pin físico 13)

print("Inicializando actuadores con gpiozero...")

# active_high=False es CRUCIAL: Los relés de Arduino se encienden con nivel BAJO (0V)
# initial_value=False asegura que arranquen APAGADOS
bomba = OutputDevice(PIN_BOMBA, active_high=False, initial_value=False)
luces = OutputDevice(PIN_LUCES, active_high=False, initial_value=False)

try:
    print("\n--- Probando BOMBA (Debería hacer CLICK y encender un LED en el shield) ---")
    print("Estado: ENCENDIENDO por 3 segundos...")
    bomba.on()  # Activa el relé mandando un nivel bajo físico
    time.sleep(3)
    print("Estado: APAGANDO...")
    bomba.off() # Apaga el relé
    
    time.sleep(1)
    
    print("\n--- Probando LUCES (Debería hacer CLICK y encender un LED en el shield) ---")
    print("Estado: ENCENDIENDO por 3 segundos...")
    luces.on()
    time.sleep(3)
    print("Estado: APAGANDO...")
    luces.off()
    
    print("\nPrueba finalizada exitosamente.")

except KeyboardInterrupt:
    print("\nPrueba cancelada por el usuario.")
finally:
    bomba.close()
    luces.close()
