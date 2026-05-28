# ADR 0001: Implement Smart Fire and Intruder Safety System

## Status

Proposed

## Context

The project will run a Smart Fire and Intruder Safety System using a Raspberry Pi 3 with GrovePi sensors. The system should monitor fire risk, intruder motion, and environmental readings, then publish live telemetry and classified threat events to an online application.

The Raspberry Pi is responsible for reading physical sensors and driving local alerts. The online backend, frontend, and database are responsible for remote monitoring, event history, arm/disarm control, and alert delivery.

The expected hardware includes:

- Raspberry Pi 3
- GrovePi board
- Grove Light Sensor v1.2
- Grove Digital PIR Motion Sensor v1.0
- Grove Temperature and Humidity Sensor v1.2
- Flame sensor
- Grove Blue LED Socket Kit v1.5

The expected features are:

- Auto-arm at night when the light sensor detects darkness
- Flame monitoring at all times
- Fire risk classification using flame, temperature, and humidity
- Intruder classification using PIR motion while armed
- Blue LED blink patterns for Safe, Intruder, Fire, and False Alarm states
- Risk engine that classifies readings as Fire, Intruder, False Alarm, or Safe
- Dashboard with live readings, threat level, arm/disarm control, and event log
- Email alerts with threat type and relevant sensor readings
- Persistent event history in a database

## Decision

Implement the project as three main software components:

1. Raspberry Pi edge application
2. Online backend API and MQTT consumer
3. Online frontend dashboard

The Raspberry Pi application will be written in Python because GrovePi support and GPIO/sensor examples are strongest in Python. It will read sensors, run a local risk engine, control a local blue LED, and communicate with the online server using MQTT.

The backend will expose an HTTP API for dashboard data, arm/disarm commands, and event history. It will also subscribe to MQTT topics to receive telemetry and threat events from the Raspberry Pi. The backend will persist readings and events in a database.

The frontend will be a web dashboard served from the online application server. It will show live readings, current system state, threat level, arm/disarm controls, and historical events.

The database will store device metadata, sensor readings, classified events, alert delivery attempts, and current system state.

## Architecture

```text
GrovePi Sensors
     |
     v
Raspberry Pi 3 Python App
     | reads sensors
     | classifies risk
     | controls blue LED
     v
Online MQTT Broker
     |
     v
Backend MQTT Consumer + REST API
     |
     v
Database
     |
     v
Frontend Dashboard
```

## Raspberry Pi Application

The Raspberry Pi application will:

- Read sensor values on a fixed interval.
- Publish telemetry to MQTT.
- Publish threat events immediately when detected.
- Subscribe to command topics for manual arm/disarm updates.
- Keep a local state machine for armed/disarmed mode.
- Auto-arm when the light sensor indicates darkness.
- Run a local risk engine so alarms can trigger even if the internet connection is slow.
- Drive local blue LED patterns.
- Retry MQTT connection when the network is unavailable.

The blue LED will communicate system state using blink patterns:

- Safe: LED off or very slow heartbeat blink
- Intruder: slow repeating blink
- Fire: fast repeating blink
- False Alarm: short double blink pattern

Recommended MQTT topics:

- `safety/{device_id}/telemetry`
- `safety/{device_id}/event`
- `safety/{device_id}/state`
- `safety/{device_id}/command`
- `safety/{device_id}/heartbeat`

Example telemetry payload:

```json
{
  "device_id": "raspi3-grovepi-01",
  "timestamp": "2026-05-28T12:00:00Z",
  "light": 102,
  "flame_detected": false,
  "temperature_c": 26.4,
  "humidity_percent": 52.0,
  "motion_detected": false,
  "armed": true,
  "threat": "Safe",
  "risk_score": 0.12
}
```

## Risk Engine

The risk engine will classify each sensor sample into one of:

- `Fire`
- `Intruder`
- `False Alarm`
- `Safe`

Initial rule-based logic will be used first. This is more appropriate for a safety project than starting with an opaque model.

Proposed fire scoring:

- Flame detected: high fire score
- High temperature: increases fire score
- Low humidity: increases fire score
- Flame + high temperature + low humidity: confirmed fire

Proposed intruder scoring:

- PIR motion while armed: intruder event
- PIR motion while disarmed: log as motion, not an intrusion
- Darkness can increase suspicion, but must not be required for intruder detection if the system is manually armed

The AI element will be implemented as a transparent risk engine first. A later version can add a trained model if enough labeled event data is collected.

Default thresholds will be provided in configuration. Users will be able to change thresholds from the dashboard, and the backend will publish updated configuration to the Raspberry Pi over MQTT.

## Backend

The backend will:

- Subscribe to MQTT telemetry and event topics.
- Validate payloads before writing to the database.
- Store sensor readings and classified events.
- Send email alerts for Fire and Intruder events.
- Expose APIs for dashboard data.
- Expose APIs for arm/disarm actions.
- Expose APIs for viewing and updating sensor thresholds.
- Publish arm/disarm commands back to MQTT.
- Publish threshold updates back to MQTT.
- Provide authentication for dashboard access.

Recommended backend API endpoints:

- `GET /api/devices`
- `GET /api/devices/{device_id}/latest`
- `GET /api/devices/{device_id}/readings`
- `GET /api/devices/{device_id}/events`
- `GET /api/devices/{device_id}/thresholds`
- `PUT /api/devices/{device_id}/thresholds`
- `POST /api/devices/{device_id}/arm`
- `POST /api/devices/{device_id}/disarm`
- `GET /api/health`

## Frontend

The frontend dashboard will show:

- Current status: Safe, Fire, Intruder, False Alarm, Offline
- Live sensor readings
- Arm/disarm toggle
- Threat level indicator
- Threshold settings
- Event log
- Alert status
- Device connectivity status

Live updates can be implemented with WebSockets or polling. Polling is acceptable for the first version. WebSockets can be added if the dashboard needs lower latency.

## Database

Use a relational database, preferably PostgreSQL, because the project has structured data and event history.

Core tables:

- `devices`
- `sensor_readings`
- `events`
- `alerts`
- `device_state`
- `thresholds`
- `users`

Minimum fields for events:

- `id`
- `device_id`
- `event_type`
- `risk_score`
- `sensor_snapshot`
- `created_at`
- `alert_sent`

## Alerting

The backend will send alerts when:

- A Fire event is classified.
- An Intruder event is classified while armed.
- The device goes offline for longer than the configured timeout.

Email will be implemented using SMTP. SMS will not be included in the first version.

## Data Retention

Raw sensor readings should be kept for a short period so the database does not grow too quickly. The first version will retain raw sensor readings for 30 days. Classified events and alert history can be kept longer because they are lower volume and useful for review.

## Work Breakdown

1. Define project structure
   - Create directories for Raspberry Pi code, backend, frontend, database migrations, and docs.
   - Define shared JSON payload contracts.

2. Implement Raspberry Pi sensor layer
   - Install GrovePi dependencies on the Raspberry Pi.
   - Create Python drivers or wrappers for light, flame, temperature/humidity, PIR, and blue LED.
   - Add a mock sensor mode for development without hardware.

3. Implement Raspberry Pi risk engine
   - Add rule-based scoring for Fire, Intruder, False Alarm, and Safe.
   - Add thresholds in a config file.
   - Allow threshold updates received from the backend.
   - Add unit tests for classification logic.

4. Implement Raspberry Pi MQTT communication
   - Publish telemetry, events, state, and heartbeat.
   - Subscribe to command topic for arm/disarm.
   - Add reconnect and offline behavior.

5. Implement backend service
   - Create REST API.
   - Add MQTT subscriber.
   - Validate incoming payloads.
   - Store readings and events.
   - Publish arm/disarm commands to MQTT.

6. Implement database
   - Create schema and migrations.
   - Add seed data for one Raspberry Pi device.
   - Add default thresholds.
   - Add a 30-day retention policy for raw sensor readings.

7. Implement alerts
   - Add email sending.
   - Store alert attempts and failures.

8. Implement frontend dashboard
   - Build live device status view.
   - Build readings panel.
   - Build threat indicator.
   - Build arm/disarm control.
   - Build threshold configuration view.
   - Build event log.

9. Test end-to-end behavior
   - Test mock sensor mode locally.
   - Test Raspberry Pi with real sensors.
   - Test MQTT messages.
   - Test dashboard updates.
   - Test alert delivery.

10. Prepare demo scenario
    - Fire event simulation.
    - Intruder event simulation.
    - Safe state.
    - False alarm scenario.
    - Online dashboard and event history review.

## Consequences

Positive consequences:

- The Raspberry Pi can trigger local alarms even if the dashboard is unreachable.
- MQTT gives a lightweight and reliable communication path for IoT telemetry.
- The online dashboard can monitor the system from anywhere.
- A rule-based risk engine is explainable and appropriate for a safety-critical prototype.

Tradeoffs:

- The system depends on internet connectivity for remote dashboard updates and alerts.
- Email delivery depends on SMTP provider reliability and correct credentials.
- The Raspberry Pi 3 has limited resources, so the edge app should stay lightweight.
- GrovePi sensor calibration will be required for reliable thresholds.
- A blue LED can only communicate state through blink patterns, not separate colors.

## Assumptions

- The Raspberry Pi 3 will run Raspberry Pi OS.
- The hardware will use Grove Light Sensor v1.2, Grove Digital PIR Motion Sensor v1.0, Grove Temperature and Humidity Sensor v1.2, a flame sensor, and Grove Blue LED Socket Kit v1.5.
- The online server will run Linux and Docker.
- MQTT traffic will be protected with username/password and TLS in production.
- The dashboard will require authentication.
- PostgreSQL will be used unless there is a strong reason to choose another database.
- The first AI version is a transparent risk engine, not a trained machine learning model.
- Users can change default thresholds from the dashboard.
- Raw sensor readings will be retained for 30 days in the first version.

## Open Questions

- None.
