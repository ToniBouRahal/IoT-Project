import json
import logging
import ssl
import threading
import time
from datetime import datetime, timezone
from typing import Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

TOPIC_TELEMETRY = "safety/{device_id}/telemetry"
TOPIC_EVENT     = "safety/{device_id}/event"
TOPIC_STATE     = "safety/{device_id}/state"
TOPIC_COMMAND   = "safety/{device_id}/command"
TOPIC_HEARTBEAT = "safety/{device_id}/heartbeat"


class MqttClient:
    def __init__(self, config: dict, on_command: Callable[[dict], None]):
        self._cfg = config
        self._device_id: str = config["device_id"]
        self._on_command = on_command
        self._connected = threading.Event()
        self._shutdown = threading.Event()

        self._client = mqtt.Client(client_id=self._device_id)
        self._client.username_pw_set(config["mqtt"]["username"], config["mqtt"]["password"])

        if config["mqtt"].get("tls", False):
            self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    # ------------------------------------------------------------------ connect

    def connect(self):
        """Start connection in a background thread with automatic reconnect."""
        t = threading.Thread(target=self._connect_loop, daemon=True)
        t.start()

    def wait_connected(self, timeout: float = 30.0) -> bool:
        """Block until MQTT is connected or timeout expires. Returns True if connected."""
        return self._connected.wait(timeout=timeout)

    def _connect_loop(self):
        delay = self._cfg["mqtt"].get("reconnect_delay", 5)
        while not self._shutdown.is_set():
            try:
                logger.info("Connecting to MQTT broker %s:%d",
                            self._cfg["mqtt"]["host"], self._cfg["mqtt"]["port"])
                self._client.connect(self._cfg["mqtt"]["host"], self._cfg["mqtt"]["port"])
                self._client.loop_forever()
            except Exception as exc:
                logger.warning("MQTT connection failed: %s — retrying in %ds", exc, delay)
            if not self._shutdown.is_set():
                time.sleep(delay)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected")
            self._connected.set()
            topic = TOPIC_COMMAND.format(device_id=self._device_id)
            client.subscribe(topic, qos=1)
        else:
            logger.warning("MQTT connect refused: rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc):
        self._connected.clear()
        if rc != 0:
            logger.warning("MQTT unexpectedly disconnected rc=%d", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self._on_command(payload)
        except Exception as exc:
            logger.warning("Failed to handle MQTT command: %s", exc)

    # ----------------------------------------------------------------- publish

    def publish_telemetry(self, reading: dict):
        topic = TOPIC_TELEMETRY.format(device_id=self._device_id)
        self._publish(topic, reading, qos=0)

    def publish_event(self, event: dict):
        topic = TOPIC_EVENT.format(device_id=self._device_id)
        self._publish(topic, event, qos=1)

    def publish_state(self, armed: bool, threat: str):
        topic = TOPIC_STATE.format(device_id=self._device_id)
        self._publish(topic, {"device_id": self._device_id, "armed": armed, "threat": threat}, qos=1)

    def publish_heartbeat(self):
        topic = TOPIC_HEARTBEAT.format(device_id=self._device_id)
        self._publish(topic, {
            "device_id": self._device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, qos=0)

    def _publish(self, topic: str, payload: dict, qos: int = 0):
        if not self._connected.is_set():
            logger.debug("MQTT not connected, skipping publish to %s", topic)
            return
        try:
            self._client.publish(topic, json.dumps(payload), qos=qos)
        except Exception as exc:
            logger.warning("Publish to %s failed: %s", topic, exc)

    def disconnect(self):
        self._shutdown.set()
        self._client.disconnect()
