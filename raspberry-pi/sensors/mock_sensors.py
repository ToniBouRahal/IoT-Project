"""Mock sensor implementations for development without hardware."""
import math
import random
import time
from .base import BaseSensor

_start = time.time()


class MockLightSensor(BaseSensor):
    """Cycles between bright (200) and dark (20) over 60 seconds."""
    def read(self) -> dict:
        elapsed = time.time() - _start
        # Oscillate: bright during first 30s, dark during next 30s
        phase = (elapsed % 60) / 60
        value = int(110 + 90 * math.cos(2 * math.pi * phase))
        return {"light": max(0, min(1023, value))}


class MockFlameSensor(BaseSensor):
    """Returns flame_detected=True for 5 seconds every 90 seconds."""
    def read(self) -> dict:
        elapsed = time.time() - _start
        flame = (elapsed % 90) > 85
        return {"flame_detected": flame}


class MockPirSensor(BaseSensor):
    """Triggers motion for 3 seconds every 45 seconds."""
    def read(self) -> dict:
        elapsed = time.time() - _start
        motion = (elapsed % 45) > 42
        return {"motion_detected": motion}


class MockTempHumiditySensor(BaseSensor):
    """Returns gently varying temperature and humidity."""
    def read(self) -> dict:
        elapsed = time.time() - _start
        temp = 24.0 + 2.0 * math.sin(elapsed / 30)
        humidity = 55.0 + 5.0 * math.cos(elapsed / 45)
        return {
            "temperature_c": round(temp, 1),
            "humidity_percent": round(humidity, 1),
        }


class MockLedController:
    def __init__(self, port: int = 5):
        self.port = port
        self._pattern = "safe"

    def set_pattern(self, pattern: str):
        if pattern != self._pattern:
            print(f"[LED] pattern -> {pattern}")
            self._pattern = pattern

    def stop(self):
        print("[LED] stopped")
