# Local MQTT Broker

Phase 5 provides a local Eclipse Mosquitto broker for development and demo use. The port is bound to 127.0.0.1 and the broker allows anonymous connections; do not expose this configuration to a public network or use it in production.

Start Mosquitto from the repository root:

    docker compose -f docker/docker-compose.yml up -d

Subscribe to all device messages in a second terminal:

    mosquitto_sub -h localhost -t 'machines/+/#' -v

Publish simulated telemetry from the repository root:

    python -m edge.mqtt_demo --condition imbalance --severity 1.0 --windows 10

The demo defaults to config/default.yaml and falls back to config/thresholds.example.yaml if config/thresholds.yaml is absent. Environment variables such as MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, MQTT_PASSWORD, and MQTT_USE_TLS override broker settings. Username and password must be supplied together.

Inspect broker output:

    docker compose -f docker/docker-compose.yml logs -f mosquitto

Stop the broker:

    docker compose -f docker/docker-compose.yml down

The named volume preserves local broker state; remove it with `docker compose -f docker/docker-compose.yml down -v` only when you want to delete that local state.
