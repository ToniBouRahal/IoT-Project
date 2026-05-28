# Deployment Guide

## Prerequisites

- Docker and Docker Compose v2 installed on the Contabo VPS
- Ports 80, 443, and 8883 open in the firewall
- DNS records pointing to the server IP:
  - `mqtt.devdungeons.com`
  - `api.devdungeons.com`
  - `dashboard.devdungeons.com`

## First-time setup

### 1. Create MQTT credentials

```bash
cd deploy

# Create the passwd file
docker run --rm -v "$PWD/mosquitto:/mosquitto" eclipse-mosquitto:2.0 \
  mosquitto_passwd -c /mosquitto/config/passwd backend

docker run --rm -v "$PWD/mosquitto:/mosquitto" eclipse-mosquitto:2.0 \
  mosquitto_passwd /mosquitto/config/passwd raspi3-grovepi-01
```

### 2. Create TLS certificates for MQTT (port 8883)

Option A — self-signed (development/testing):
```bash
mkdir -p deploy/mosquitto/certs
openssl req -newkey rsa:2048 -nodes -x509 -days 365 \
  -keyout deploy/mosquitto/certs/server.key \
  -out deploy/mosquitto/certs/server.crt \
  -subj "/CN=mqtt.devdungeons.com"
cp deploy/mosquitto/certs/server.crt deploy/mosquitto/certs/ca.crt
```

Option B — Let's Encrypt cert (copy from Traefik's `/letsencrypt/acme.json` after first deploy).

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in all passwords and SMTP credentials
```

### 4. Deploy

```bash
docker compose up -d
```

### 5. Run database migrations

Migrations run automatically via the `migrate` service. Verify with:
```bash
docker logs migrate
```

## Updating

```bash
docker compose build backend frontend
docker compose up -d
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f mqtt
```

## Connecting the Raspberry Pi

Set these environment variables on the Pi before starting the edge app:

```bash
MQTT_HOST=mqtt.devdungeons.com
MQTT_PORT=8883
MQTT_PASSWORD=<raspi3-grovepi-01 password>
```

The Pi uses TLS by default (`tls: true` in `config.yaml`). If using a self-signed cert, copy `ca.crt` to the Pi and point the paho TLS config to it.

## Backup

PostgreSQL data is in the `postgres-data` Docker volume. Back it up with:
```bash
docker exec postgres pg_dump -U safety safetydb > backup_$(date +%Y%m%d).sql
```
