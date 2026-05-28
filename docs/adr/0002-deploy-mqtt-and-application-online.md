# ADR 0002: Deploy MQTT Broker and Application Online

## Status

Proposed

## Context

The Smart Fire and Intruder Safety System needs an online deployment where:

- The MQTT broker runs on an online server as a container.
- The backend runs on the online server.
- The frontend runs on the online server.
- The database stores readings, events, dashboard users, and alert history.
- The Raspberry Pi connects securely to the online MQTT broker.
- Users access the dashboard through a browser.

The deployment will run on a Contabo Linux VPS. The public hostnames will be:

- `mqtt.devdungeons.com`
- `api.devdungeons.com`
- `dashboard.devdungeons.com`

The deployment should be simple enough for a student or prototype project, but structured enough to be extended later.

## Decision

Deploy the online system using Docker containers on a Linux server.

The online server will run:

- MQTT broker container
- Backend API container
- Frontend container
- PostgreSQL database container
- Traefik reverse proxy container for HTTPS routing

Selected services:

- MQTT broker: Eclipse Mosquitto
- Reverse proxy: Traefik
- Database: PostgreSQL
- Backend: containerized API service
- Frontend: containerized web app

Docker Compose will be used for the first deployment because it is easier to operate than Kubernetes for a single-server project.

## Deployment Architecture

```text
Internet
   |
   v
Traefik Reverse Proxy with HTTPS
   |
   +--> dashboard.devdungeons.com --> Frontend
   |
   +--> api.devdungeons.com -------> Backend API
                                      |
                                      v
                                  PostgreSQL

Raspberry Pi 3
   |
   v
MQTT over TLS
   |
   v
mqtt.devdungeons.com --> Mosquitto MQTT Broker
   |
   v
Backend MQTT Consumer
```

## Network Ports

Expose only the ports needed from the server:

- `80`: HTTP for certificate challenge or redirect
- `443`: HTTPS dashboard and API
- `8883`: MQTT over TLS

Avoid exposing:

- PostgreSQL port to the public internet
- Backend internal port directly
- Mosquitto non-TLS port in production

## Security

The deployment will use:

- HTTPS for frontend and backend traffic.
- MQTT over TLS for Raspberry Pi communication.
- MQTT username/password authentication.
- No MQTT client certificates in the first version.
- Separate MQTT users or credentials per device.
- Backend authentication for dashboard users.
- Environment variables or Docker secrets for credentials.
- Firewall rules allowing only required ports.

The MQTT broker should only allow each Raspberry Pi to publish and subscribe to its own topics where possible.

Example topic permission pattern:

- Device can publish to `safety/{device_id}/telemetry`
- Device can publish to `safety/{device_id}/event`
- Device can publish to `safety/{device_id}/state`
- Device can publish to `safety/{device_id}/heartbeat`
- Device can subscribe to `safety/{device_id}/command`
- Backend can subscribe and publish to all safety topics

## Docker Compose Services

The first deployment should include these services:

- `reverse-proxy`
- `mqtt`
- `backend`
- `frontend`
- `postgres`

The containers should share an internal Docker network. Only Traefik HTTP/HTTPS entrypoints and the MQTT TLS port should be publicly reachable.

Recommended persistent volumes:

- Mosquitto config and data
- PostgreSQL data
- Traefik certificates
- Backend logs if file logging is used

## MQTT Broker

Use Eclipse Mosquitto because it is lightweight, common, and reliable for MQTT projects.

Required configuration:

- Disable anonymous access.
- Enable password authentication.
- Configure TLS listener on port `8883`.
- Use username/password authentication over TLS for the first version.
- Add ACL rules for device and backend topics.
- Persist broker data if retained messages are used.

Retained messages can be useful for current device state, but event messages should not rely only on retained messages because all events must be persisted by the backend.

## Backend Deployment

The backend container will:

- Connect to PostgreSQL using an internal Docker hostname.
- Connect to Mosquitto using an internal Docker hostname.
- Expose HTTP only to the reverse proxy.
- Run database migrations during deployment or through a separate migration command.
- Load alert provider credentials from environment variables.

The backend should have health checks for:

- API availability
- Database connection
- MQTT connection

## Frontend Deployment

The frontend will run as a dedicated container and will be routed by Traefik at `dashboard.devdungeons.com`.

## Database Deployment

PostgreSQL will run as a container for the prototype deployment.

Minimum operational requirements:

- Persistent volume for database files
- Regular backups
- Restricted network access
- Strong database password
- Migration process

For the first version, the database will remain containerized on the Contabo server.

## Alert Delivery

The backend will need outbound internet access for SMTP email delivery.

Required environment variables will likely include:

- SMTP host, port, username, and password
- Email sender address
- Alert recipient email addresses

Any SMTP provider is acceptable for the first version as long as these settings are provided and test emails can be delivered reliably.

## Work Breakdown

1. Prepare the online server
   - Provision a Contabo Linux VPS.
   - Install Linux updates.
   - Install Docker and Docker Compose.
   - Configure firewall for ports `80`, `443`, and `8883`.
   - Create a deployment user.

2. Configure DNS
   - Point `mqtt.devdungeons.com` to the Contabo server IP.
   - Point `api.devdungeons.com` to the Contabo server IP.
   - Point `dashboard.devdungeons.com` to the Contabo server IP.

3. Create Docker Compose deployment
   - Define services for reverse proxy, MQTT, backend, frontend, and PostgreSQL.
   - Define internal Docker network.
   - Define persistent volumes.
   - Add health checks.

4. Configure HTTPS
   - Configure Traefik.
   - Issue TLS certificates using Let's Encrypt.
   - Redirect HTTP to HTTPS.

5. Configure MQTT broker
   - Create Mosquitto config.
   - Create MQTT password file.
   - Create ACL rules.
   - Enable TLS on port `8883`.
   - Test publish and subscribe from a development machine.

6. Deploy database
   - Start PostgreSQL container.
   - Configure database name, user, and password.
   - Run migrations.
   - Verify persistent storage.

7. Deploy backend
   - Build backend image.
   - Configure environment variables.
   - Connect backend to PostgreSQL and MQTT.
   - Verify health endpoint.
   - Verify MQTT consumer receives test messages.

8. Deploy frontend
   - Build frontend image.
   - Serve frontend through Traefik at `dashboard.devdungeons.com`.
   - Configure API base URL.
   - Verify dashboard loads and authenticates.

9. Connect Raspberry Pi
   - Install device certificate or CA certificate if needed.
   - Configure MQTT host, port, device ID, username, and password.
   - Start Raspberry Pi service.
   - Verify telemetry appears in MQTT broker, backend, database, and dashboard.

10. Configure alerts
   - Add SMTP credentials.
   - Send test Fire and Intruder alerts.
   - Verify alert attempts are stored in the database.

11. Add operations and maintenance
    - Configure database backups.
    - Configure log rotation.
    - Add restart policies.
    - Document deployment and rollback commands.
    - Add monitoring for container health and disk usage.

12. Final acceptance test
    - Verify dashboard over HTTPS.
    - Verify MQTT over TLS.
    - Verify Raspberry Pi telemetry.
    - Verify arm/disarm command path.
    - Verify Fire alert path.
    - Verify Intruder alert path.
    - Verify event history persists after container restart.

## Consequences

Positive consequences:

- Docker Compose keeps deployment understandable and repeatable.
- Mosquitto is a good fit for lightweight Raspberry Pi telemetry.
- TLS and authentication protect device communication.
- Running all online components on one server is cost-effective for a prototype.
- Traefik provides automatic HTTPS routing for the API and dashboard containers.

Tradeoffs:

- A single server is a single point of failure.
- Containerized PostgreSQL requires careful backup handling.
- TLS setup for MQTT adds configuration complexity.
- Scaling later may require moving to managed database, managed MQTT, or orchestration.
- Username/password over TLS is simpler than client certificates, but device credentials must be protected carefully.

## Assumptions

- The online server is a Contabo Linux VPS with a public IP address.
- DNS will use `mqtt.devdungeons.com`, `api.devdungeons.com`, and `dashboard.devdungeons.com`.
- Docker Compose is acceptable for the first version.
- The MQTT broker and web application can run on the same online server.
- The Raspberry Pi will have internet access.
- All online components will run as containers.
- Traefik will handle HTTPS routing for the web application and API.
- MQTT will use username/password authentication over TLS.
- Email alerts will use SMTP, and any working SMTP provider is acceptable for the first version.

## Open Questions

- None.
