# System Architecture

**Industrial Condition Monitoring Node — Architecture Document**  
*Phase 1 — Version 0.1*

---

## 1. Overview

This document describes the architecture of a low-cost predictive maintenance and condition monitoring node designed to retrofit legacy industrial machinery. The system collects vibration (3-axis acceleration) and temperature data at the edge, performs signal processing and explainable anomaly detection, publishes telemetry over MQTT, and presents live and historical data through a monitoring dashboard.

The architecture is **modular by design**: each layer communicates through well-defined interfaces so components can be developed, tested, and replaced independently. A software simulator stands in for physical hardware during development.

---

## 2. Design Principles

| Principle | Implementation |
|-----------|----------------|
| Modularity | Separate packages for simulator, edge processing, backend, dashboard, firmware |
| Hardware abstraction | Sensor and transport interfaces allow simulator ↔ ESP32 swap |
| Explainability | Fault status derived from named features with documented thresholds |
| Incremental delivery | Ten development phases; each phase produces a testable artifact |
| Honest scope | Limitations documented; no fake "AI" or inflated diagnostic claims |
| Configuration over hardcoding | Thresholds, device IDs, and broker settings in YAML / env vars |

---

## 3. Layer Architecture

### 3.1 Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: DATA ACQUISITION                                        │
│                                                                  │
│  MachineSimulator ──┐                                            │
│  ESP32 Firmware  ───┼──▶ Raw samples: ax[], ay[], az[], temp    │
│                     │    Metadata: timestamp, device_id, seq     │
└─────────────────────┼────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 2: EDGE SIGNAL PROCESSING                                  │
│                                                                  │
│  Filter → Time-domain features → FFT → Dominant frequency        │
│  Output: FeatureVector                                           │
└─────────────────────┼────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 3: ANOMALY DETECTION                                       │
│                                                                  │
│  ThresholdChecker + BaselineTracker + CompositeScorer            │
│  Output: MachineStatus (NORMAL | WARNING | CRITICAL)             │
│          AnomalyScore, triggered_rules[]                         │
└─────────────────────┼────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: MQTT PUBLISHING                                         │
│                                                                  │
│  TelemetryPublisher → machines/{id}/telemetry                    │
│  StatusPublisher    → machines/{id}/status (retained)            │
│  AlertPublisher     → machines/{id}/alerts (on state change)     │
└─────────────────────┼────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 5: BACKEND                                                 │
│                                                                  │
│  MQTT Subscriber → Validator → Processor → Database              │
│  REST API + WebSocket → Dashboard                                │
│  AlertManager → notifications                                    │
└─────────────────────┼────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 6: DASHBOARD                                               │
│                                                                  │
│  Live gauges, trend charts, alert panel, device status           │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

#### Simulator (`simulator/`) — Phase 2

Generates physics-informed synthetic vibration and temperature signals for defined machine conditions. Not random noise — each fault type modifies the signal in a recognisable way (harmonics, impulses, drift).

**Interface:** Implements `MachineDataSource` — same contract as firmware.

#### Edge Processing (`edge/`) — Phases 3–4

Reference implementation in Python (validated before porting to firmware C++).

| Module | Responsibility |
|--------|----------------|
| `sampling` | Buffer management, windowing, overlap |
| `filtering` | Butterworth bandpass, anti-aliasing considerations |
| `features/time_domain` | Mean, RMS, peak, peak-to-peak, std dev, crest factor |
| `features/frequency_domain` | FFT, dominant frequency, spectral peaks |
| `anomaly/thresholds` | Configurable limit checking |
| `anomaly/baseline` | Rolling baseline and z-score deviation |
| `anomaly/scorer` | Composite anomaly score → status classification |
| `mqtt/publisher` | JSON serialization and topic routing |

#### Backend (`backend/`) — Phase 6

| Module | Responsibility |
|--------|----------------|
| `mqtt/subscriber` | Subscribe to `machines/+/telemetry`, `+/alerts` |
| `validation` | JSON schema validation, range checks |
| `persistence` | SQLite storage of telemetry and alerts |
| `api/routes` | REST endpoints for history, devices, alerts |
| `api/websocket` | Push live telemetry to dashboard |
| `alerts` | Deduplication, escalation, optional webhook |

#### Dashboard (`dashboard/`) — Phase 7

Single-page application with industrial monitoring aesthetic:

- Machine status banner (NORMAL / WARNING / CRITICAL)
- Real-time gauges: temperature, RMS, peak, dominant frequency
- Time-series charts with configurable range
- Active alerts panel with feature-level explanation
- Device connectivity indicator (MQTT last-seen)

#### Firmware (`firmware/`) — Phase 8

| Module | Responsibility |
|--------|----------------|
| `drivers/accelerometer` | I2C/SPI sensor read |
| `drivers/temperature` | 1-Wire or I2C temperature read |
| `sampling` | Timer-driven acquisition at configured rate |
| `dsp/` | Ported filter + feature extraction (CMSIS-DSP where applicable) |
| `anomaly/` | Same logic as Python reference, fixed-point where needed |
| `mqtt/` | WiFi connection, publish loop |
| `config/` | NVS-stored device ID and broker settings |
| `diagnostics` | Watchdog, heap monitor, error counters |

---

## 4. Interface Contracts

### 4.1 MachineDataSource

Abstraction shared by simulator and firmware:

```python
class MachineDataSource(Protocol):
    def read_window(self) -> RawSampleWindow: ...
    def read_temperature(self) -> float: ...
    @property
    def device_id(self) -> str: ...
    @property
    def sample_rate_hz(self) -> int: ...
```

### 4.2 FeatureVector

```python
@dataclass
class FeatureVector:
    timestamp: datetime
    device_id: str
    temperature_c: float
    vibration_x: float      # instantaneous or window mean — documented per publish mode
    vibration_y: float
    vibration_z: float
    vibration_rms: float
    vibration_peak: float
    vibration_peak_to_peak: float
    vibration_std: float
    crest_factor: float
    dominant_frequency_hz: float
```

### 4.3 AnomalyResult

```python
@dataclass
class AnomalyResult:
    status: Literal["NORMAL", "WARNING", "CRITICAL"]
    anomaly_score: float          # 0.0 – 1.0
    triggered_rules: list[str]    # e.g. ["vibration_rms > warning", "z_score_temperature"]
    explanation: str              # Human-readable summary
```

### 4.4 AnomalyScorer (Pluggable)

```python
class AnomalyScorer(Protocol):
    def score(self, features: FeatureVector) -> AnomalyResult: ...
```

Phase 4 implements `ThresholdScorer`. Future ML models implement the same interface.

---

## 5. Communication Architecture

### 5.1 MQTT

- **Broker:** Eclipse Mosquitto (local development and demo deployment)
- **QoS:** 1 for telemetry and alerts (at-least-once delivery)
- **Retained messages:** Device status topic only
- **Payload format:** JSON (UTF-8)

See [mqtt-architecture.md](mqtt-architecture.md) for topic hierarchy and schemas.

### 5.2 Backend API

REST (FastAPI) for historical queries; WebSocket for live dashboard push.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/devices` | GET | List registered devices |
| `/api/devices/{id}/latest` | GET | Latest telemetry snapshot |
| `/api/devices/{id}/history` | GET | Time-range telemetry |
| `/api/alerts` | GET | Active and recent alerts |
| `/ws/telemetry` | WS | Live telemetry stream |

---

## 6. Data Storage

**SQLite** with two primary tables (Phase 6):

```sql
-- telemetry: time-series measurements (one row per publish interval)
-- alerts: fault events with status, score, and triggered rules
```

Retention policy configurable (`telemetry_retention_days` in config). For portfolio scale this is sufficient. Production upgrade path: PostgreSQL with TimescaleDB hypertables or InfluxDB.

---

## 7. Configuration Architecture

Configuration is layered:

1. **`config/default.yaml`** — system defaults (committed)
2. **`config/thresholds.yaml`** — per-machine limits (gitignored, copied from example)
3. **`config/devices.yaml`** — device registry (gitignored, copied from example)
4. **`config/local.yaml`** — environment overrides (gitignored, optional)
5. **`.env`** — secrets and deployment-specific values (gitignored)

Environment variables override YAML where specified (e.g. `MQTT_BROKER_HOST`, `DEVICE_ID`).

---

## 8. Deployment Topology (Local Development)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Simulator  │────▶│  Mosquitto  │◀────│   Backend   │
│  (Python)   │ MQTT│  :1883      │ MQTT│  (FastAPI)  │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           │              ┌─────▼─────┐
                           │              │  SQLite   │
                           │              └─────┬─────┘
                           │                    │ REST/WS
                           │              ┌─────▼─────┐
                           │              │ Dashboard │
                           │              │  :5173    │
                           └──────────────┴───────────┘
```

Docker Compose will orchestrate Mosquitto + backend for Phase 5+. Simulator runs as a standalone Python process.

---

## 9. Security Considerations (Planned)

| Concern | Mitigation |
|---------|------------|
| MQTT credentials | Environment variables; TLS optional for production |
| API access | CORS restricted to dashboard origin; auth added in future phase |
| Firmware | NVS encryption for WiFi credentials (ESP32) |
| Input validation | JSON schema validation on all MQTT payloads |

This is a portfolio/demo system — full IEC 62443 compliance is out of scope but documented as a future improvement.

---

## 10. Testing Strategy

| Level | Scope | Phase |
|-------|-------|-------|
| Unit | Filter coefficients, feature calculations, threshold logic | 3–4 |
| Integration | Simulator → edge → MQTT (mock broker) | 5 |
| End-to-end | Full pipeline with Mosquitto, backend, dashboard | 9 |
| Firmware | Hardware-in-the-loop against Python reference outputs | 8–9 |

---

## 11. Phase Dependencies

```
Phase 1 (Architecture)
    └── Phase 2 (Simulator)
            └── Phase 3 (Signal Processing)
                    └── Phase 4 (Fault Detection)
                            └── Phase 5 (MQTT)
                                    └── Phase 6 (Backend)
                                            └── Phase 7 (Dashboard)
                                                    └── Phase 8 (Firmware)
                                                            └── Phase 9 (E2E Testing)
                                                                    └── Phase 10 (Documentation)
```

Each phase produces independently testable artifacts. No phase skips its predecessor.

---

## 12. Related Documents

- [Engineering Decisions](engineering-decisions.md)
- [Signal Processing](signal-processing.md)
- [MQTT Architecture](mqtt-architecture.md)
- [Fault Detection](fault-detection.md)
- [Hardware Design](hardware.md)
- [Development Roadmap](roadmap.md)
- [Limitations](limitations.md)
