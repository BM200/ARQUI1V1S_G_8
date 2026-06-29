try:
    import RPi.GPIO as GPIO  # type: ignore
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False

    class _GPIOStub:
        BCM = "BCM"
        OUT = "OUT"
        IN = "IN"
        HIGH = 1
        LOW = 0
        PUD_UP = "PUD_UP"
        FALLING = "FALLING"

        def setwarnings(self, *args, **kwargs): pass
        def setmode(self, *args, **kwargs): pass
        def setup(self, *args, **kwargs): pass
        def output(self, *args, **kwargs): pass
        def input(self, *args, **kwargs): return self.HIGH
        def cleanup(self, *args, **kwargs): pass
        def add_event_detect(self, *args, **kwargs): pass

    GPIO = _GPIOStub()


def nivel_encendido(rele_activo_en_low: bool = True):
    return GPIO.LOW if rele_activo_en_low else GPIO.HIGH


def nivel_apagado(rele_activo_en_low: bool = True):
    return GPIO.HIGH if rele_activo_en_low else GPIO.LOW 