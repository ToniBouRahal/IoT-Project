from .base import BaseSensor

try:
    import grovepi
    _GROVEPI_AVAILABLE = True
except ImportError:
    _GROVEPI_AVAILABLE = False

LIGHT_SENSOR_PORT = 0  # Analog A0


class LightSensor(BaseSensor):
    def __init__(self, port: int = LIGHT_SENSOR_PORT):
        self.port = port

    def read(self) -> dict:
        if not _GROVEPI_AVAILABLE:
            raise RuntimeError("grovepi not available; use MockLightSensor in mock_mode")
        value = grovepi.analogRead(self.port)
        return {"light": int(value)}
