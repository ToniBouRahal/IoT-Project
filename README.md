# Smart Fire and Intruder Safety System

An IoT safety system built for a Raspberry Pi 3 with GrovePi sensors. The Raspberry Pi reads local fire, motion, light, temperature, and humidity signals, classifies the current risk, controls a blue LED status indicator, and publishes telemetry to an online MQTT broker. The online application stores readings and events, sends email alerts, and provides a dashboard for monitoring, arm/disarm control, thresholds, and event history.

## Features

- Raspberry Pi 3 edge app with GrovePi sensor support
- Mock sensor mode for development without hardware
- Rule-based risk engine for `Safe`, `Fire`, `Intruder`, and `False Alarm`
- Night auto-arm using the light sensor
- Manual arm/disarm commands from the dashboard
- Blue LED blink patterns for local status
- MQTT telemetry, events, state, heartbeat, and commands
- FastAPI backend with JWT authentication
- PostgreSQL database with Alembic migrations
- Email alerts through SMTP
- Static web dashboard served by Nginx
- Docker Compose deployment with Traefik, Mosquitto, backend, frontend, and PostgreSQL

## Hardware

The Raspberry Pi node is designed for:

- Raspberry Pi 3
- GrovePi board
- Grove Light Sensor v1.2
- Grove Digital PIR Motion Sensor v1.0
- Grove Temperature and Humidity Sensor v1.2
- Flame sensor
- Grove Blue LED Socket Kit v1.5

Default GrovePi wiring:

| Sensor | GrovePi Port |
| --- | --- |
| Grove Light Sensor v1.2 | `A0` |
| Flame Sensor | `D2` |
| Grove Digital PIR Motion Sensor v1.0 | `D3` |
| Grove Temperature and Humidity Sensor v1.2 | `D4` |
| Grove Blue LED Socket Kit v1.5 | `D5` |

## Architecture

```text
GrovePi Sensors
   |
   v
Raspberry Pi Edge App
   | MQTT over TLS
   v
mqtt.devdungeons.com
Mosquitto MQTT Broker
   |
   v
FastAPI Backend + MQTT Consumer
   |
   v
PostgreSQL
   |
   v
Dashboard at dashboard.devdungeons.com
```

The deployment target is a Contabo Linux VPS using:

- `mqtt.devdungeons.com` for MQTT over TLS
- `api.devdungeons.com` for the backend API
- `dashboard.devdungeons.com` for the frontend dashboard
- Traefik for HTTPS routing
- Docker Compose for all online services

## Repository Layout

```text
backend/       FastAPI API, MQTT subscriber, database models, migrations, email alerts
frontend/      Static dashboard served by Nginx
raspberry-pi/  Raspberry Pi edge application, sensors, MQTT client, risk engine, tests
deploy/        Docker Compose, Traefik, Mosquitto config, deployment guide
docs/adr/      Architecture Decision Records
```

## MQTT Topics

The system uses device-scoped MQTT topics:

```text
safety/{device_id}/telemetry
safety/{device_id}/event
safety/{device_id}/state
safety/{device_id}/command
safety/{device_id}/heartbeat
```

The default device ID is:

```text
raspi3-grovepi-01
```

## Raspberry Pi App

Install Python dependencies:

```bash
cd raspberry-pi
pip install -r requirements.txt
```

On a real Raspberry Pi with GrovePi, install the GrovePi library:

```bash
curl -kL dexterindustries.com/update_grovepi | bash
```

Run with real hardware:

```bash
python main.py
```

Run with mock sensors:

```bash
MOCK_MODE=true python main.py
```

Connect to the online MQTT broker:

```bash
MQTT_HOST=mqtt.devdungeons.com MQTT_PORT=8883 MQTT_PASSWORD=<device-password> python main.py
```

Configuration lives in [raspberry-pi/config.yaml](/home/it-laptop/Iot-Project/raspberry-pi/config.yaml). Important environment overrides include `DEVICE_ID`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_PASSWORD`, and `MOCK_MODE`.

## Backend

The backend is a FastAPI service that:

- Receives telemetry and events through the MQTT subscriber
- Stores devices, readings, events, alerts, state, thresholds, and users
- Sends SMTP email alerts for Fire and Intruder events
- Exposes authenticated API endpoints under `/api`
- Publishes arm/disarm and threshold update commands back to MQTT

Run locally with a configured database and MQTT broker:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Main API groups:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/devices`
- `GET /api/devices/{device_id}/latest`
- `GET /api/devices/{device_id}/readings`
- `GET /api/devices/{device_id}/events`
- `POST /api/devices/{device_id}/arm`
- `POST /api/devices/{device_id}/disarm`
- `GET /api/devices/{device_id}/thresholds`
- `PUT /api/devices/{device_id}/thresholds`
- `GET /api/health`

## Frontend

The frontend is a static dashboard served by Nginx in Docker. It supports:

- Login
- Device selection
- Live status polling
- Threat banner
- Latest sensor readings
- Arm/disarm controls
- Threshold editing
- Event history

For deployed usage, access:

```text
https://dashboard.devdungeons.com
```

The dashboard calls the API through `/api` by default.

Because the production API hostname is `api.devdungeons.com`, deployment should either route `/api` from `dashboard.devdungeons.com` to the backend or set `window.API_BASE_URL` to `https://api.devdungeons.com/api` before `static/js/app.js` loads.

## Online Deployment

Deployment files are in [deploy/](/home/it-laptop/Iot-Project/deploy).

Prerequisites:

- Contabo Linux VPS
- Docker and Docker Compose v2
- DNS records for `mqtt.devdungeons.com`, `api.devdungeons.com`, and `dashboard.devdungeons.com`
- Open firewall ports `80`, `443`, and `8883`

First-time setup:

```bash
cd deploy
cp .env.example .env
```

Edit `.env` and set database passwords, MQTT credentials, SMTP settings, JWT secret, and Let's Encrypt email.

Create Mosquitto credentials as described in [deploy/README.md](/home/it-laptop/Iot-Project/deploy/README.md), then start the stack:

```bash
docker compose up -d
```

Migrations run through the `migrate` service:

```bash
docker logs migrate
```

Useful logs:

```bash
docker compose logs -f backend
docker compose logs -f mqtt
docker compose logs -f frontend
```

## Default Seed Data

The first migration seeds:

- Device: `raspi3-grovepi-01`
- Admin user: `admin@devdungeons.com`
- Default password: `admin123`
- Default risk thresholds

Change the default admin password before exposing the dashboard publicly.

## Testing

Run Raspberry Pi risk engine tests:

```bash
cd raspberry-pi
python -m pytest tests/ -v
```

## Documentation

Architecture decisions:

- [ADR 0001: Implement Smart Fire and Intruder Safety System](/home/it-laptop/Iot-Project/docs/adr/0001-implement-smart-fire-intruder-safety-system.md)
- [ADR 0002: Deploy MQTT Broker and Application Online](/home/it-laptop/Iot-Project/docs/adr/0002-deploy-mqtt-and-application-online.md)

Deployment details:

- [Deployment Guide](/home/it-laptop/Iot-Project/deploy/README.md)
- [Raspberry Pi Edge App Guide](/home/it-laptop/Iot-Project/raspberry-pi/README.md)
