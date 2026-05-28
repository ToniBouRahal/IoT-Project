import threading
import time

try:
    import grovepi
    _GROVEPI_AVAILABLE = True
except ImportError:
    _GROVEPI_AVAILABLE = False

LED_PORT = 5  # Digital D5

# Pattern definitions: list of (on_seconds, off_seconds) tuples, repeated forever.
# None means the LED stays off.
PATTERNS = {
    "safe": None,                          # off (heartbeat handled separately)
    "intruder": [(1.0, 1.0)],             # slow blink
    "fire": [(0.2, 0.2)],                 # fast blink
    "false_alarm": [(0.1, 0.1, 0.1, 0.8)], # double-blink: on/off/on/pause
}


def _write(port: int, value: int):
    if _GROVEPI_AVAILABLE:
        grovepi.digitalWrite(port, value)


class LedController:
    def __init__(self, port: int = LED_PORT):
        self.port = port
        self._current_pattern: str = "safe"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        if _GROVEPI_AVAILABLE:
            grovepi.pinMode(self.port, "OUTPUT")

    def set_pattern(self, pattern: str):
        if pattern not in PATTERNS:
            raise ValueError(f"Unknown LED pattern: {pattern!r}")
        if pattern == self._current_pattern:
            return
        self._current_pattern = pattern
        self._restart_thread()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        _write(self.port, 0)

    def _restart_thread(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        pattern = PATTERNS[self._current_pattern]
        if pattern is None:
            # Safe: heartbeat — one brief blink every 4 seconds
            _write(self.port, 0)
            while not self._stop_event.is_set():
                _write(self.port, 1)
                if self._stop_event.wait(0.1):
                    break
                _write(self.port, 0)
                self._stop_event.wait(4.0)
            _write(self.port, 0)
            return

        steps = pattern[0]
        # Steps alternate on/off. For double-blink we have 4 values.
        on_off = True
        idx = 0
        while not self._stop_event.is_set():
            _write(self.port, 1 if on_off else 0)
            if self._stop_event.wait(steps[idx % len(steps)]):
                break
            on_off = not on_off
            idx += 1
        _write(self.port, 0)
