# Raspberry Pi Edge Application

Smart Fire and Intruder Safety System — edge sensor node.

## Setup

```bash
pip install -r requirements.txt
```

On a real Raspberry Pi with GrovePi, also install the GrovePi library:

```bash
curl -kL dexterindustries.com/update_grovepi | bash
```

## Running

```bash
# With real hardware
python main.py

# Without hardware (mock sensors)
MOCK_MODE=true python main.py

# Custom MQTT connection
MQTT_HOST=localhost MQTT_PORT=1883 MQTT_PASSWORD=secret MOCK_MODE=true python main.py
```

## Configuration

Edit `config.yaml` to change MQTT settings and risk thresholds. All fields can be overridden via environment variables:

| Variable       | Description                        |
|----------------|------------------------------------|
| `DEVICE_ID`    | Device identifier                  |
| `MQTT_HOST`    | MQTT broker hostname               |
| `MQTT_PORT`    | MQTT broker port                   |
| `MQTT_PASSWORD`| MQTT password                      |
| `MOCK_MODE`    | `true` to use mock sensors         |

## Tests

```bash
cd raspberry-pi
python -m pytest tests/ -v
```

## Sensor Wiring

| Sensor                  | GrovePi Port |
|-------------------------|--------------|
| Grove Light Sensor v1.2 | A0           |
| Flame Sensor            | D2           |
| Grove PIR Motion v1.0   | D3           |
| Grove Temp+Humidity v1.2| D4           |
| Grove Blue LED v1.5     | D5           |
