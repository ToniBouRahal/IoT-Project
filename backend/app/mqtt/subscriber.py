"""MQTT subscriber that runs in a background thread and bridges messages to async handlers."""
import asyncio
import json
import logging
import ssl
import threading

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.config import settings
from app.database import AsyncSessionLocal
from app.schemas.telemetry import TelemetryPayload, EventPayload
from app.services import telemetry as telemetry_svc, events as events_svc
from app.services.commands import set_mqtt_client
from app.alerts.email import send_event_alerts

logger = logging.getLogger(__name__)

_loop: asyncio.AbstractEventLoop | None = None
_connected = False


def _on_connect(client, userdata, flags, rc):
    global _connected
    if rc == 0:
        _connected = True
        logger.info("Backend MQTT connected")
        client.subscribe("safety/+/telemetry", qos=0)
        client.subscribe("safety/+/event", qos=1)
        client.subscribe("safety/+/state", qos=0)
        client.subscribe("safety/+/heartbeat", qos=0)
    else:
        logger.warning("Backend MQTT connect refused: rc=%d", rc)


def _on_disconnect(client, userdata, rc):
    global _connected
    _connected = False
    if rc != 0:
        logger.warning("Backend MQTT disconnected unexpectedly: rc=%d", rc)


def _on_message(client, userdata, msg):
    if _loop is None:
        return
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        logger.warning("Could not parse MQTT message on %s", msg.topic)
        return

    topic = msg.topic
    # Route by topic suffix
    if topic.endswith("/telemetry"):
        asyncio.run_coroutine_threadsafe(_handle_telemetry(payload), _loop)
    elif topic.endswith("/event"):
        asyncio.run_coroutine_threadsafe(_handle_event(payload), _loop)
    elif topic.endswith("/heartbeat"):
        asyncio.run_coroutine_threadsafe(_handle_heartbeat(payload), _loop)


async def _handle_telemetry(payload: dict):
    try:
        data = TelemetryPayload(**payload)
    except ValidationError as exc:
        logger.warning("Invalid telemetry payload: %s", exc)
        return
    async with AsyncSessionLocal() as db:
        await telemetry_svc.save_telemetry(db, data)


async def _handle_event(payload: dict):
    try:
        data = EventPayload(**payload)
    except ValidationError as exc:
        logger.warning("Invalid event payload: %s", exc)
        return
    async with AsyncSessionLocal() as db:
        event = await events_svc.save_event(db, data)
        if data.event_type in ("Fire", "Possible Fire", "Intruder"):
            await send_event_alerts(db, event)


async def _handle_heartbeat(payload: dict):
    from datetime import datetime, timezone
    from sqlalchemy import update
    from app.models import Device

    device_id = payload.get("device_id")
    if not device_id:
        return
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(last_seen=datetime.now(timezone.utc))
        )
        await db.commit()


def _mqtt_thread(client: mqtt.Client):
    client.loop_forever()


def start_subscriber(loop: asyncio.AbstractEventLoop):
    """Start the MQTT subscriber background thread."""
    global _loop
    _loop = loop

    client = mqtt.Client(client_id="backend-subscriber")
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    if settings.mqtt_tls:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message

    try:
        client.connect(settings.mqtt_host, settings.mqtt_port)
    except Exception as exc:
        logger.warning("Could not connect backend MQTT at startup: %s (will not retry)", exc)
        return

    set_mqtt_client(client)

    t = threading.Thread(target=_mqtt_thread, args=(client,), daemon=True)
    t.start()
    logger.info("MQTT subscriber thread started")


def is_connected() -> bool:
    return _connected
