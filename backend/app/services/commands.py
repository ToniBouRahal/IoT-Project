"""Publish arm/disarm and threshold commands to MQTT."""
import json
import logging

logger = logging.getLogger(__name__)

# Set by the MQTT subscriber module after client is ready
_mqtt_client = None


def set_mqtt_client(client):
    global _mqtt_client
    _mqtt_client = client


def _publish(device_id: str, payload: dict):
    topic = f"safety/{device_id}/command"
    if _mqtt_client is None:
        logger.warning("MQTT client not available, cannot publish command to %s", topic)
        return
    try:
        _mqtt_client.publish(topic, json.dumps(payload), qos=1)
        logger.info("Published command to %s: %s", topic, payload)
    except Exception as exc:
        logger.error("Failed to publish MQTT command: %s", exc)


def publish_arm(device_id: str):
    _publish(device_id, {"command": "arm"})


def publish_disarm(device_id: str):
    _publish(device_id, {"command": "disarm"})


def publish_threshold_update(device_id: str, thresholds: dict):
    _publish(device_id, {"command": "update_thresholds", "thresholds": thresholds})
