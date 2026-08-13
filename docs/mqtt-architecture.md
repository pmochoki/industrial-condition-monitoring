# MQTT Architecture

**Phase 1 — Design Specification**  
*Implementation: Phase 5 (publisher), Phase 6 (subscriber)*

---

## 1. Overview

MQTT is the communication layer between edge nodes (simulator or ESP32 firmware) and the backend. It provides lightweight pub/sub messaging suitable for IoT telemetry with intermittent connectivity.

**Broker:** Eclipse Mosquitto (local development)  
**Protocol:** MQTT v3.1.1 (v5 optional future upgrade)  
**Transport:** TCP (TLS optional for production)

---

## 2. Topic Hierarchy

```
machines/
└── {device_id}/
    ├── telemetry      # Periodic measurements (QoS 1, not retained)
    ├── status         # Device health summary (QoS 1, retained)
    └── alerts         # Fault events (QoS 1, not retained)
```

### Topic Definitions

| Topic | Direction | QoS | Retained | Rate | Purpose |
|-------|-----------|-----|----------|------|---------|
| `machines/{device_id}/telemetry` | Edge → Backend | 1 | No | ~1 Hz | Measurement + features |
| `machines/{device_id}/status` | Edge → Backend | 1 | Yes | On change + heartbeat | Connectivity, firmware version |
| `machines/{device_id}/alerts` | Edge → Backend | 1 | No | On state change | Fault notifications |

### Backend Subscriptions

```
machines/+/telemetry
machines/+/status
machines/+/alerts
```

The `+` wildcard matches any single device ID level.

### Design Rationale

- **Device-scoped topics** allow multi-node expansion without topic redesign
- **Retained status** lets the dashboard show last-known device state on connect
- **Separate alerts topic** prevents alert messages being lost in high-rate telemetry stream
- **No command topic in Phase 1–7** — future: `machines/{device_id}/command` for remote config

---

## 3. Payload Schemas

All payloads are JSON (UTF-8). Schemas will be enforced by Pydantic models in backend (Phase 6).

### 3.1 Telemetry Message

**Topic:** `machines/{device_id}/telemetry`

```json
{
  "device_id": "machine-001",
  "timestamp": "2026-08-13T12:00:00.000Z",
  "sequence": 12345,
  "source": "simulator",
  "temperature_c": 45.2,
  "vibration": {
    "x": 0.012,
    "y": 0.008,
    "z": 1.045,
    "rms": 0.052,
    "peak": 0.148,
    "peak_to_peak": 0.291,
    "std_dev": 0.051,
    "crest_factor": 2.85,
    "dominant_frequency_hz": 20.0
  },
  "machine_status": "NORMAL",
  "anomaly_score": 0.12,
  "triggered_rules": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | string | Yes | Unique device identifier |
| `timestamp` | ISO 8601 UTC | Yes | Measurement time |
| `sequence` | integer | Yes | Monotonic counter for gap detection |
| `source` | string | Yes | `"simulator"` or `"hardware"` |
| `temperature_c` | float | Yes | Temperature in °C |
| `vibration.x/y/z` | float | Yes | Window mean acceleration per axis (g) |
| `vibration.rms` | float | Yes | Resultant RMS (g) |
| `vibration.peak` | float | Yes | Resultant peak (g) |
| `vibration.peak_to_peak` | float | Yes | Resultant peak-to-peak (g) |
| `vibration.std_dev` | float | Yes | Resultant standard deviation (g) |
| `vibration.crest_factor` | float | Yes | Peak / RMS |
| `vibration.dominant_frequency_hz` | float | Yes | Dominant spectral peak (Hz) |
| `machine_status` | enum | Yes | `NORMAL`, `WARNING`, `CRITICAL` |
| `anomaly_score` | float | Yes | Composite score 0.0–1.0 |
| `triggered_rules` | string[] | Yes | Active rule names (empty if normal) |

### 3.2 Status Message

**Topic:** `machines/{device_id}/status`  
**Retained:** Yes

```json
{
  "device_id": "machine-001",
  "timestamp": "2026-08-13T12:00:00.000Z",
  "online": true,
  "firmware_version": "0.0.0-sim",
  "uptime_s": 3600,
  "sample_rate_hz": 2048,
  "last_sequence": 12345,
  "wifi_rssi": null,
  "errors": []
}
```

Published on:
- Initial connection (retained)
- Status change (online/offline via LWT — see below)
- Periodic heartbeat (every 60 s)

### 3.3 Alert Message

**Topic:** `machines/{device_id}/alerts`

```json
{
  "device_id": "machine-001",
  "timestamp": "2026-08-13T12:05:00.000Z",
  "alert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "severity": "WARNING",
  "previous_status": "NORMAL",
  "current_status": "WARNING",
  "anomaly_score": 0.52,
  "triggered_rules": [
    "vibration_rms_g > warning (0.14 > 0.12)",
    "crest_factor approaching warning (4.8)"
  ],
  "explanation": "Vibration RMS exceeded warning threshold. Elevated crest factor suggests impulsive content.",
  "features": {
    "vibration_rms": 0.14,
    "crest_factor": 4.8,
    "temperature_c": 52.1,
    "dominant_frequency_hz": 20.0
  }
}
```

Alerts are published only on **status transitions** (NORMAL→WARNING, WARNING→CRITICAL, etc.) to avoid alert flooding.

---

## 4. Connection Management

### 4.1 Last Will and Testament (LWT)

Edge clients register a LWT on connect:

- **Topic:** `machines/{device_id}/status`
- **Payload:** `{"device_id": "...", "online": false, "timestamp": "..."}`
- **QoS:** 1, Retained: true

Backend and dashboard treat LWT as device offline.

### 4.2 Authentication

Development: anonymous access on local Mosquitto.  
Production (future): username/password via environment variables; TLS on port 8883.

```
MQTT_USERNAME=edge-node-001
MQTT_PASSWORD=<from env, not committed>
MQTT_USE_TLS=true
```

---

## 5. Message Flow

```
Edge Node                          Mosquitto                    Backend
    │                                  │                            │
    │── CONNECT (LWT=offline) ────────▶│                            │
    │── PUBLISH status (retained) ────▶│── deliver retained ───────▶│
    │                                  │                            │
    │── PUBLISH telemetry (1 Hz) ─────▶│── forward ────────────────▶│
    │                                  │                     validate │
    │                                  │                     store    │
    │                                  │                     push WS  │
    │                                  │                            │
    │── PUBLISH alert (on change) ────▶│── forward ────────────────▶│
    │                                  │                     store    │
    │                                  │                     notify   │
```

---

## 6. Error Handling

| Scenario | Edge Behaviour | Backend Behaviour |
|----------|---------------|-------------------|
| Broker unreachable | Buffer N messages locally (firmware: limited RAM); retry connect | N/A |
| Invalid JSON | N/A | Log error, increment rejection counter, do not store |
| Sequence gap | N/A | Log warning, store anyway |
| Duplicate sequence | N/A | Deduplicate by (device_id, sequence) |
| Unknown device_id | N/A | Store with flag; optionally auto-register |

---

## 7. Local Development Setup (Phase 5+)

Mosquitto will run via Docker Compose:

```yaml
# docker/docker-compose.yml (Phase 5 — placeholder)
services:
  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
```

---

## 8. Related Documents

- [Architecture](architecture.md)
- [Fault Detection](fault-detection.md)
- [Engineering Decisions — ED-06](engineering-decisions.md)
