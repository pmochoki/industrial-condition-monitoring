# Backend API & MQTT Subscriber

FastAPI backend that ingests MQTT telemetry, validates and stores data, and exposes REST/WebSocket endpoints for the dashboard.

**Status:** Not yet implemented — begins in Phase 6.

## Planned Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── mqtt/
│   └── subscriber.py       # MQTT client, topic handlers
├── models/
│   ├── telemetry.py        # Pydantic schemas
│   └── database.py         # SQLAlchemy models
├── api/
│   ├── routes.py           # REST endpoints
│   └── websocket.py        # Live telemetry push
├── services/
│   ├── persistence.py      # Database operations
│   └── alerts.py           # Alert manager
└── config.py               # Settings from YAML + env
```

See [docs/architecture.md](../docs/architecture.md) and [docs/mqtt-architecture.md](../docs/mqtt-architecture.md).
