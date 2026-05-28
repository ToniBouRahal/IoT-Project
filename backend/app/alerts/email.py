import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Alert, Event

logger = logging.getLogger(__name__)


def _build_body(event: Event) -> str:
    snap = event.sensor_snapshot
    lines = [
        f"ALERT: {event.event_type} detected",
        f"Device:    {event.device_id}",
        f"Time:      {event.created_at.isoformat()}",
        f"Risk score:{event.risk_score:.3f}",
        "",
        "Sensor readings at time of event:",
        f"  Flame detected:   {snap.get('flame_detected')}",
        f"  Temperature:      {snap.get('temperature_c')} °C",
        f"  Humidity:         {snap.get('humidity_percent')} %",
        f"  Motion detected:  {snap.get('motion_detected')}",
        f"  Light level:      {snap.get('light')}",
        f"  System armed:     {snap.get('armed')}",
        "",
        "Please check the dashboard for details.",
    ]
    return "\n".join(lines)


async def send_event_alerts(db: AsyncSession, event: Event):
    """Send email alerts for a Fire or Intruder event and record results."""
    recipients = settings.alert_recipients_list
    if not recipients:
        logger.warning("No alert recipients configured, skipping email for event %s", event.id)
        return

    body = _build_body(event)
    subject = f"[ALERT] {event.event_type} detected — {event.device_id}"

    all_ok = True
    for recipient in recipients:
        alert = Alert(
            event_id=event.id,
            alert_type="email",
            recipient=recipient,
        )
        db.add(alert)
        await db.flush()

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from
            msg["To"] = recipient

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.sendmail(settings.smtp_from, [recipient], msg.as_string())

            alert.success = True
            alert.sent_at = datetime.now(timezone.utc)
            logger.info("Alert email sent to %s for event %s", recipient, event.id)
        except Exception as exc:
            alert.success = False
            alert.error_message = str(exc)
            all_ok = False
            logger.error("Failed to send alert to %s: %s", recipient, exc)

    if all_ok:
        event.alert_sent = True

    await db.commit()
