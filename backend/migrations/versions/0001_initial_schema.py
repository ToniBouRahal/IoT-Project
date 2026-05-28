"""Initial schema with seed data

Revision ID: 0001
Revises:
Create Date: 2026-05-28

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"])

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("light", sa.Integer(), nullable=True),
        sa.Column("flame_detected", sa.Boolean(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("humidity_percent", sa.Float(), nullable=True),
        sa.Column("motion_detected", sa.Boolean(), nullable=True),
        sa.Column("armed", sa.Boolean(), nullable=True),
        sa.Column("threat", sa.String(32), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_readings_device_id", "sensor_readings", ["device_id"])
    op.create_index("ix_sensor_readings_timestamp", "sensor_readings", ["timestamp"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("sensor_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_device_id", "events", ["device_id"])
    op.create_index("ix_events_created_at", "events", ["created_at"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("recipient", sa.String(256), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "device_state",
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("armed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("threat", sa.String(32), nullable=False, server_default="Safe"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_reading", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"]),
        sa.PrimaryKeyConstraint("device_id"),
    )

    op.create_table(
        "thresholds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("light_dark_threshold", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("flame_fire_score", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("temp_high_c", sa.Float(), nullable=False, server_default="40"),
        sa.Column("temp_extreme_c", sa.Float(), nullable=False, server_default="60"),
        sa.Column("humidity_low_pct", sa.Float(), nullable=False, server_default="30"),
        sa.Column("fire_confirm_score", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("fire_alarm_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.device_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Seed: default device
    device_id_val = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO devices (id, device_id, name, created_at)
        VALUES ('{device_id_val}', 'raspi3-grovepi-01', 'GrovePi Sensor Node', NOW())
    """)

    # Seed: default thresholds for device
    threshold_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO thresholds (id, device_id, light_dark_threshold, flame_fire_score,
            temp_high_c, temp_extreme_c, humidity_low_pct, fire_confirm_score, fire_alarm_score, updated_at)
        VALUES ('{threshold_id}', 'raspi3-grovepi-01', 50, 0.7, 40.0, 60.0, 30.0, 0.8, 0.5, NOW())
    """)

    # Seed: admin user (password = admin123, bcrypt hashed)
    # Hash was generated with passlib.context.CryptContext(schemes=["bcrypt"]).hash("admin123")
    admin_id = str(uuid.uuid4())
    hashed = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6nkFUGpQDu"
    op.execute(f"""
        INSERT INTO users (id, email, hashed_password, is_active, created_at)
        VALUES ('{admin_id}', 'admin@devdungeons.com', '{hashed}', true, NOW())
    """)


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("thresholds")
    op.drop_table("device_state")
    op.drop_table("alerts")
    op.drop_table("events")
    op.drop_table("sensor_readings")
    op.drop_table("devices")
