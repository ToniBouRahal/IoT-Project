from .base import BaseSensor

try:
    import grovepi
    _GROVEPI_AVAILABLE = True
except ImportError:
    _GROVEPI_AVAILABLE = False

PIR_SENSOR_PORT = 3  # Digital D3


class PirSensor(BaseSensor):
    def __init__(self, port: int = PIR_SENSOR_PORT):
        self.port = port
        if _GROVEPI_AVAILABLE:
            grovepi.pinMode(self.port, "INPUT")

    def read(self) -> dict:
        if not _GROVEPI_AVAILABLE:
            raise RuntimeError("grovepi not available; use MockPirSensor in mock_mode")
        raw = grovepi.digitalRead(self.port)
        return {"motion_detected": bool(raw)}
