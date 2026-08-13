# Docker Services

Local service orchestration for MQTT broker and backend.

**Status:** Docker Compose will be added in Phase 5.

## Planned Services

```yaml
# docker-compose.yml (Phase 5)
services:
  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf

  # backend: added in Phase 6
  # dashboard: added in Phase 7 (or run via npm dev server)
```

Start services (when implemented):

```bash
docker compose up -d
```
