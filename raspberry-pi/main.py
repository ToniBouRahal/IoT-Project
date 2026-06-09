"""Raspberry Pi edge application — Smart Fire and Intruder Safety System."""
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone

import yaml

from risk_engine import RiskEngine, Thresholds
from state_machine import SystemState
from mqtt_client import MqttClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    # Allow environment overrides
    cfg["device_id"] = os.getenv("DEVICE_ID", cfg.get("device_id", "raspi3-grovepi-01"))
    cfg["mqtt"]["host"] = os.getenv("MQTT_HOST", cfg["mqtt"]["host"])
    cfg["mqtt"]["port"] = int(os.getenv("MQTT_PORT", cfg["mqtt"]["port"]))
    cfg["mqtt"]["password"] = os.getenv("MQTT_PASSWORD", cfg["mqtt"].get("password", ""))
    mock_env = os.getenv("MOCK_MODE")
    if mock_env is not None:
        cfg["mock_mode"] = mock_env.lower() in ("1", "true", "yes")
    return cfg


def build_sensors(cfg: dict):
    if cfg.get("mock_mode"):
        logger.info("Running in MOCK sensor mode")
        from sensors.mock_sensors import (
            MockLightSensor, MockFlameSensor, MockPirSensor,
            MockTempHumiditySensor, MockLedController,
        )
        return (
            MockLightSensor(),
            MockFlameSensor(),
            MockPirSensor(),
            MockTempHumiditySensor(),
            MockLedController(),
        )
    from sensors import LightSensor, FlameSensor, PirSensor, TempHumiditySensor, LedController
    return (
        LightSensor(),
        FlameSensor(),
        PirSensor(),
        TempHumiditySensor(),
        LedController(),
    )


def main():
    cfg = load_config()
    thresholds = Thresholds.from_dict(cfg.get("thresholds", {}))
    state = SystemState(thresholds)
    engine = RiskEngine()

    light_sensor, flame_sensor, pir_sensor, th_sensor, led = build_sensors(cfg)

    last_threat = "Safe"
    last_heartbeat = 0.0

    def on_command(payload: dict):
        cmd = payload.get("command")
        if cmd == "arm":
            state.manual_arm()
        elif cmd == "disarm":
            state.manual_disarm()
        elif cmd == "update_thresholds":
            state.update_thresholds(payload.get("thresholds", {}))
        else:
            logger.warning("Unknown command: %s", cmd)

    mqtt_client = MqttClient(cfg, on_command=on_command)
    mqtt_client.connect()

    # Send a heartbeat immediately after connecting so the backend pushes back
    # the latest saved thresholds before the first sensor cycle runs.
    if mqtt_client.wait_connected(timeout=30):
        mqtt_client.publish_heartbeat()
        last_heartbeat = time.time()
    else:
        logger.warning("MQTT did not connect within 30s — starting with default thresholds")
        last_heartbeat = 0.0

    stop_event = threading.Event()

    def _shutdown(sig, frame):
        logger.info("Shutdown signal received")
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    interval = cfg["mqtt"].get("telemetry_interval", 10)
    heartbeat_interval = cfg["mqtt"].get("heartbeat_interval", 30)

    logger.info("Starting sensor loop (interval=%ds, device_id=%s)", interval, cfg["device_id"])

    while not stop_event.is_set():
        loop_start = time.time()

        try:
            light    = light_sensor.read()["light"]
            flame    = flame_sensor.read()["flame_detected"]
            pir      = pir_sensor.read()["motion_detected"]
            th       = th_sensor.read()
            temp     = th["temperature_c"]
            humidity = th["humidity_percent"]
        except Exception as exc:
            logger.error("Sensor read error: %s", exc)
            stop_event.wait(timeout=interval)
            continue

        state.auto_arm(light)

        threat, risk_score = engine.classify(
            light, flame, temp, humidity, pir, state.armed, state.thresholds
        )

        # Map threat to LED pattern
        pattern_map = {
            "Safe":          "safe",
            "Intruder":      "intruder",
            "Fire":          "fire",
            "Possible Fire": "possible_fire",
            "False Alarm":   "false_alarm",
        }
        led.set_pattern(pattern_map.get(threat, "safe"))

        now = datetime.now(timezone.utc).isoformat()
        telemetry = {
            "device_id": cfg["device_id"],
            "timestamp": now,
            "light": light,
            "flame_detected": flame,
            "temperature_c": temp,
            "humidity_percent": humidity,
            "motion_detected": pir,
            "armed": state.armed,
            "threat": threat,
            "risk_score": risk_score,
        }
        mqtt_client.publish_telemetry(telemetry)
        logger.info("Telemetry: %s", telemetry)

        # Publish event on threat transition to Fire, Possible Fire, or Intruder
        if threat != last_threat and threat in ("Fire", "Possible Fire", "Intruder"):
            event = {
                "device_id": cfg["device_id"],
                "timestamp": now,
                "event_type": threat,
                "risk_score": risk_score,
                "sensor_snapshot": {
                    "light": light,
                    "flame_detected": flame,
                    "temperature_c": temp,
                    "humidity_percent": humidity,
                    "motion_detected": pir,
                    "armed": state.armed,
                },
            }
            mqtt_client.publish_event(event)
            logger.warning("EVENT published: %s (score=%.3f)", threat, risk_score)

        if threat != last_threat:
            mqtt_client.publish_state(state.armed, threat)
            last_threat = threat

        now_ts = time.time()
        if now_ts - last_heartbeat >= heartbeat_interval:
            mqtt_client.publish_heartbeat()
            last_heartbeat = now_ts

        elapsed = time.time() - loop_start
        sleep_time = max(0.0, interval - elapsed)
        stop_event.wait(timeout=sleep_time)

    led.stop()
    mqtt_client.disconnect()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
