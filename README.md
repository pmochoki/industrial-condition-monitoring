# Industrial Condition Monitoring Node

**Predictive maintenance and condition monitoring for legacy industrial machinery — built as a portfolio-grade, end-to-end engineering project.**

[![Status](https://img.shields.io/badge/status-Phase%201%20Architecture-blue)](/docs/roadmap.md)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#)

---

## Problem

Legacy industrial machinery often lacks integrated condition monitoring. Unplanned failures cause downtime, safety risks, and unnecessary maintenance cost. Full industrial CM systems (vibration analysers, SCADA integrations, cloud platforms) are expensive and require specialist commissioning.

This project demonstrates a **practical, low-cost retrofit approach**: an edge node that samples vibration and temperature, performs on-device signal processing, publishes telemetry over MQTT, and feeds a live monitoring dashboard with explainable fault detection.

---

## Proposed Solution

A modular system with clear separation between hardware, edge processing, communication, backend, and dashboard layers. During development, a **physics-informed machine simulator** replaces physical hardware so the full pipeline can be built and tested without sensors.

```
Machine → Sensors → Edge Node → Signal Processing → Anomaly Detection
    → MQTT → Backend → Database → Dashboard → Alerts
```

| Layer | Technology (planned) | Status |
|-------|---------------------|--------|
| Machine simulator | Python | Phase 2 |
| Edge signal processing | Python (reference) / C++ (firmware) | Phase 3–4 |
| MQTT telemetry | Eclipse Mosquitto | Phase 5 |
| Backend | Python, FastAPI | Phase 6 |
| Database | SQLite | Phase 6 |
| Dashboard | React, TypeScript | Phase 7 |
| Firmware | ESP32 / STM32 | Phase 8 |

See [Architecture](docs/architecture.md) for the full system design.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PHYSICAL / SIMULATED                          │
│  ┌──────────┐   ┌─────────────┐   ┌─────────────┐                       │
│  │ Machine  │──▶│ IMU / Accel │   │ Temperature │                       │
│  └──────────┘   └──────┬──────┘   └──────┬──────┘                       │
│                        └────────┬────────┘                              │
│                                 ▼                                       │
│                    ┌────────────────────────┐                           │
│                    │   Edge Node (ESP32)    │                           │
│                    │  • Sampling            │                           │
│                    │  • Filtering           │                           │
│                    │  • Feature extraction  │                           │
│                    │  • Anomaly scoring     │                           │
│                    └───────────┬────────────┘                           │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │ MQTT
                                 ▼
                    ┌────────────────────────┐
                    │   MQTT Broker          │
                    │   (Mosquitto)          │
                    └───────────┬────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │  Backend    │   │  Database   │   │  Dashboard  │
     │  (FastAPI)  │──▶│  (SQLite)   │◀──│  (React)    │
     └─────────────┘   └─────────────┘   └─────────────┘
              │
              ▼
     ┌─────────────┐
     │   Alerts    │
     └─────────────┘
```

---

## Hardware (Planned — Phase 8)

| Component | Recommended | Alternative |
|-----------|-------------|-------------|
| Microcontroller | **ESP32** (WiFi, dual-core) | STM32 + external WiFi module |
| Vibration sensor | 3-axis MEMS accelerometer (e.g. ADXL345, MPU6050) | Industrial IEPE accelerometer + conditioning (future) |
| Temperature | Digital sensor (e.g. DS18B20, TMP117) | Thermocouple + ADC |

The firmware architecture will mirror the Python edge modules so signal processing logic can be validated in simulation before deployment.

Details: [Hardware Design](docs/hardware.md)

---

## Software Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Simulator & edge (dev) | Python 3.11+ | NumPy/SciPy ecosystem, rapid iteration |
| Backend API | FastAPI | Async, WebSocket support, OpenAPI docs |
| MQTT client | paho-mqtt | Standard, lightweight |
| Database | SQLite | Zero-infra local deployment; upgrade path to PostgreSQL |
| Dashboard | React + TypeScript | Custom industrial UI for portfolio demonstration |
| Broker | Eclipse Mosquitto | Industry-standard, easy local deployment |
| Firmware | ESP-IDF / Arduino (ESP32) | WiFi + MQTT libraries available |

Engineering rationale: [Engineering Decisions](docs/engineering-decisions.md)

---

## Signal Processing Pipeline

```
Raw acceleration (x, y, z)
    → Anti-aliasing / bandpass filter
    → Time-domain features (mean, RMS, peak, peak-to-peak, std dev, crest factor)
    → FFT → dominant frequency
    → Feature vector
    → Anomaly scoring → NORMAL | WARNING | CRITICAL
```

**Sampling rate:** 2048 Hz (configurable)  
**FFT window:** 1024 samples (0.5 s at 2048 Hz)

Assumptions and limitations are documented honestly — this is a **demonstration system**, not a certified diagnostic instrument.

Details: [Signal Processing](docs/signal-processing.md)

---

## MQTT Architecture

| Topic | Purpose |
|-------|---------|
| `machines/{device_id}/telemetry` | Periodic measurement + features |
| `machines/{device_id}/status` | Connectivity and health summary (retained) |
| `machines/{device_id}/alerts` | Event-driven fault notifications |

Details: [MQTT Architecture](docs/mqtt-architecture.md)

---

## Fault Detection

Explainable, threshold-based detection with statistical deviation from baseline:

- **NORMAL** — all features within configured limits
- **WARNING** — one or more features exceed warning thresholds or z-score limits
- **CRITICAL** — severe threshold breach or multiple concurrent warnings

Architecture supports future ML model integration via a pluggable scorer interface.

Details: [Fault Detection](docs/fault-detection.md)

---

## Repository Structure

```
industrial-condition-monitoring/
├── config/                 # YAML configuration (defaults + examples)
├── docs/                   # Architecture and engineering documentation
├── simulator/              # Machine signal simulator (Phase 2)
├── edge/                   # Signal processing & anomaly detection (Phase 3–4)
├── backend/                # MQTT subscriber, API, persistence (Phase 6)
├── dashboard/              # Live monitoring UI (Phase 7)
├── firmware/               # ESP32 / STM32 firmware (Phase 8)
│   ├── esp32/
│   └── stm32/
├── tests/                  # Unit and integration tests
├── scripts/                # Development and deployment helpers
└── docker/                 # Local service orchestration (Phase 5+)
```

---

## Development Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Architecture, docs, config structure | **Complete** |
| 2 | Machine simulator | **Complete** |
| 3 | Signal processing modules + tests | Next |
| 4 | Fault detection | Planned |
| 5 | MQTT publishing | Planned |
| 6 | Backend + database | Planned |
| 7 | Dashboard | Planned |
| 8 | Firmware architecture | Planned |
| 9 | End-to-end integration testing | Planned |
| 10 | Final documentation | Planned |

Full roadmap: [docs/roadmap.md](docs/roadmap.md)

---

## Setup (Phase 2 — Machine Simulator)

The simulator requires Python 3.11+:

```bash
git clone https://github.com/pmochoki/industrial-condition-monitoring.git
cd industrial-condition-monitoring
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Generate reproducible CSV samples:

```bash
python -m simulator --condition imbalance --severity 0.5 --output sample.csv
```

Run the simulator behavior tests:

```bash
python -m pytest -q
```

The implementation status and next milestone are tracked in [docs/roadmap.md](docs/roadmap.md).

---

## Demonstration (Planned)

The completed system will demonstrate:

1. Simulated machine running under normal conditions
2. Injection of fault scenarios (imbalance, misalignment, bearing degradation, overheating)
3. Real-time telemetry via MQTT
4. Live dashboard with historical trends
5. Explainable alerts with feature-level reasoning

---

## Limitations

This project prioritises **practical engineering demonstration** over certified diagnostic accuracy:

- MEMS accelerometers on a microcontroller cannot match industrial IEPE sensor + DAQ quality
- 2048 Hz sampling is adequate for demo scenarios but insufficient for all bearing defect frequencies
- Threshold-based detection is explainable but not as sensitive as envelope analysis or ML on large datasets
- SQLite is suitable for single-node deployment, not multi-site enterprise scale

Full discussion: [Limitations](docs/limitations.md)

---

## Future Improvements

- Envelope demodulation for bearing fault frequencies
- OTA firmware updates
- Multi-node fleet management
- PostgreSQL / TimescaleDB for production time-series storage
- ML-based anomaly detection (Isolation Forest, autoencoder) via pluggable scorer
- IEC 62443 / industrial security hardening

---

## Author

**Peter Mochoki** — Embedded systems, mechatronics, and industrial automation portfolio project.

LinkedIn project post: [Predictive Maintenance & Condition Monitoring Node](https://lnkd.in/p/dp6w967a)

---

## License

MIT License — see [LICENSE](LICENSE) *(to be added in Phase 10)*.
