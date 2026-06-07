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

mkdir -p mosquitto/config

# Create the passwd file and add the backend user (-c = create, -it = interactive password prompt)
docker run --rm -it -v "$PWD/mosquitto:/mosquitto" eclipse-mosquitto:2.0 \
  mosquitto_passwd -c /mosquitto/config/passwd backend

# Add the Raspberry Pi user (no -c, appends to existing file)
docker run --rm -it -v "$PWD/mosquitto:/mosquitto" eclipse-mosquitto:2.0 \
  mosquitto_passwd /mosquitto/config/passwd raspi3-grovepi-01
```

### 2. TLS for MQTT (port 8883)

Traefik terminates TLS on port 8883 using the same Let's Encrypt cert it manages via Cloudflare DNS challenge, then forwards plain MQTT to Mosquitto on port 1883 internally. No certificates need to be generated or copied manually — Traefik handles renewal automatically.

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

`config.yaml` already has the correct host, port, username, and TLS settings. The only value you need to supply is the password:

```bash
export MQTT_PASSWORD=<raspi3-grovepi-01 password>
python main.py
```

TLS is terminated by Traefik using a valid Let's Encrypt cert, so no custom CA certificate is needed on the Pi.

## Backup

PostgreSQL data is in the `postgres-data` Docker volume. Back it up with:
```bash
docker exec postgres pg_dump -U safety safetydb > backup_$(date +%Y%m%d).sql
```
