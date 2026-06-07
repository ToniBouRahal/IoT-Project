from .base import BaseSensor

try:
    import grovepi
    _GROVEPI_AVAILABLE = True
except ImportError:
    _GROVEPI_AVAILABLE = False

FLAME_SENSOR_PORT = 2  # Digital D2


class FlameSensor(BaseSensor):
    def __init__(self, port: int = FLAME_SENSOR_PORT):
        self.port = port
        if _GROVEPI_AVAILABLE:
            grovepi.pinMode(self.port, "INPUT")

    def read(self) -> dict:
        if not _GROVEPI_AVAILABLE:
            raise RuntimeError("grovepi not available; use MockFlameSensor in mock_mode")
        # HIGH signal = flame detected on this module (active HIGH)
        raw = grovepi.digitalRead(self.port)
        return {"flame_detected": raw == 1}
