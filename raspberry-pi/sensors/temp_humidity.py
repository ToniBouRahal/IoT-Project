from .base import BaseSensor

try:
    import grovepi
    _GROVEPI_AVAILABLE = True
except ImportError:
    _GROVEPI_AVAILABLE = False

TEMP_HUMIDITY_PORT = 4  # Digital D4
DHT_MODULE_TYPE = 0    # 0 = DHT11 (Grove Temp+Humidity v1.2)


class TempHumiditySensor(BaseSensor):
    def __init__(self, port: int = TEMP_HUMIDITY_PORT, module_type: int = DHT_MODULE_TYPE):
        self.port = port
        self.module_type = module_type

    def read(self) -> dict:
        if not _GROVEPI_AVAILABLE:
            raise RuntimeError("grovepi not available; use MockTempHumiditySensor in mock_mode")
        [temp, humidity] = grovepi.dht(self.port, self.module_type)
        return {
            "temperature_c": float(temp),
            "humidity_percent": float(humidity),
        }
