# Development Roadmap

**Industrial Condition Monitoring Node**

Each phase produces a testable artifact. Phases are sequential — do not skip ahead.

---

## Phase Overview

| Phase | Name | Deliverable | Status |
|-------|------|-------------|--------|
| 1 | Architecture | Docs, config, directory structure | **Complete** |
| 2 | Machine Simulator | Physics-informed signal generator | Planned |
| 3 | Signal Processing | Filter, features, FFT + unit tests | Planned |
| 4 | Fault Detection | Threshold scorer + simulator tests | Planned |
| 5 | MQTT | Telemetry publisher + Mosquitto setup | Planned |
| 6 | Backend | MQTT subscriber, API, SQLite storage | Planned |
| 7 | Dashboard | Live industrial monitoring UI | Planned |
| 8 | Firmware | ESP32 architecture + driver stubs | Planned |
| 9 | Integration Testing | Full pipeline E2E tests | Planned |
| 10 | Documentation | Final docs, demo guide, LICENSE | Planned |

---

## Phase 1 — Architecture ✅

**Goal:** Establish project foundation before any implementation.

**Deliverables:**
- [x] README.md with problem statement, architecture overview, and roadmap
- [x] Architecture document with layer design and interface contracts
- [x] Engineering decisions document with rationale and trade-offs
- [x] Signal processing design specification
- [x] MQTT topic hierarchy and JSON schemas
- [x] Fault detection design specification
- [x] Hardware design specification
- [x] Configuration structure (YAML + .env)
- [x] Directory structure with phase placeholders
- [x] .gitignore

**Exit criteria:** Repository is cloneable, documentation is reviewable by an automation/embedded engineer, and Phase 2 can begin without architectural ambiguity.

---

## Phase 2 — Machine Simulator

**Goal:** Generate realistic synthetic vibration and temperature data for defined fault conditions.

**Deliverables:**
- `simulator/` Python package
- Machine model: shaft speed, harmonics, noise floor
- Fault models: normal, excessive vibration, imbalance, misalignment, bearing degradation, temperature increase, sudden events, sensor noise
- Configurable fault severity (0.0–1.0)
- CLI entry point: `python -m simulator --condition imbalance --severity 0.5`
- Reproducible output via random seed
- Implements `MachineDataSource` interface

**Tests:**
- Normal condition: stable RMS within expected range
- Imbalance: dominant frequency at 1× shaft speed
- Each fault type produces distinguishable feature changes

**Exit criteria:** Simulator produces plottable signals that visually and statistically differ by fault type.

---

## Phase 3 — Signal Processing

**Goal:** Implement reusable edge processing modules with validated numerical output.

**Deliverables:**
- `edge/` Python package
- Butterworth bandpass filter
- Time-domain features: mean, RMS, peak, peak-to-peak, std dev, crest factor
- FFT with Hanning window, dominant frequency extraction
- Processing pipeline orchestrator
- Unit tests with known inputs (sine waves, impulses, DC offset)

**Exit criteria:** All unit tests pass; features match hand-calculated expected values within tolerance.

---

## Phase 4 — Fault Detection

**Goal:** Classify machine status using explainable threshold and statistical methods.

**Deliverables:**
- `edge/anomaly/` modules: ThresholdChecker, BaselineTracker, CompositeScorer, StatusClassifier
- `ThresholdScorer` implementing `AnomalyScorer` interface
- Integration tests: simulator fault → expected status level
- Configurable thresholds loaded from YAML

**Exit criteria:** Each simulated fault condition triggers the expected status level with documented triggered rules.

---

## Phase 5 — MQTT

**Goal:** Publish processed telemetry to Mosquitto.

**Deliverables:**
- `edge/mqtt/` publisher module
- Mosquitto Docker Compose service
- Telemetry, status, and alert publishing per schema
- LWT for offline detection
- CLI demo: simulator → processing → MQTT → console subscriber

**Exit criteria:** Messages visible in `mosquitto_sub -t 'machines/+/#' -v` with valid JSON matching schema.

---

## Phase 6 — Backend

**Goal:** Ingest MQTT telemetry, persist data, expose REST/WebSocket API.

**Deliverables:**
- `backend/` FastAPI application
- MQTT subscriber with JSON validation (Pydantic)
- SQLite persistence (telemetry + alerts tables)
- REST endpoints: devices, latest, history, alerts
- WebSocket endpoint for live dashboard push
- Alert manager with deduplication

**Exit criteria:** Backend stores telemetry from Phase 5 publisher; REST and WebSocket endpoints return valid data.

---

## Phase 7 — Dashboard

**Goal:** Live industrial monitoring dashboard.

**Deliverables:**
- `dashboard/` React + TypeScript application
- Machine status banner (NORMAL / WARNING / CRITICAL)
- Real-time gauges: temperature, RMS, peak, dominant frequency
- Historical trend charts (configurable time range)
- Active alerts panel with feature-level explanations
- Device connectivity indicator
- Industrial aesthetic (dark theme, high-contrast status colours)

**Exit criteria:** Dashboard displays live simulator data via WebSocket; historical charts load from REST API.

---

## Phase 8 — Firmware Architecture

**Goal:** ESP32 firmware structure mirroring Python edge modules.

**Deliverables:**
- `firmware/esp32/` project skeleton (PlatformIO or ESP-IDF)
- Driver interfaces for accelerometer and temperature
- Stub implementations with TODO markers
- Pre-computed filter coefficients header
- MQTT client with LWT
- NVS configuration storage
- Documentation for building and flashing

**Exit criteria:** Firmware compiles and connects to MQTT; publishes stub or simulator-fed data. Sensor drivers marked TODO until hardware available.

---

## Phase 9 — Integration Testing

**Goal:** Validate the complete pipeline end-to-end.

**Deliverables:**
- Integration test script: start Mosquitto → backend → simulator → verify DB → verify API
- Fault injection test: cycle through all fault conditions, verify alert generation
- Test documentation

**Exit criteria:** Full pipeline runs locally with one command; all fault conditions produce expected alerts in dashboard.

---

## Phase 10 — Final Documentation

**Goal:** Portfolio-ready repository.

**Deliverables:**
- Updated README with setup instructions, demo guide, and screenshots
- LICENSE file (MIT)
- Demo video or GIF (optional)
- Known limitations and future improvements finalised
- Code review and cleanup pass

**Exit criteria:** An engineer unfamiliar with the project can clone, set up, run the demo, and understand the engineering decisions within 30 minutes.

---

## Timeline Estimate

| Phase | Estimated Effort |
|-------|-----------------|
| 1 | 1 session ✅ |
| 2 | 1–2 sessions |
| 3 | 1–2 sessions |
| 4 | 1 session |
| 5 | 1 session |
| 6 | 2 sessions |
| 7 | 2–3 sessions |
| 8 | 2–3 sessions |
| 9 | 1 session |
| 10 | 1 session |

*Estimates assume incremental development with review between phases.*

---

## Current Status

**Phase 1 is complete.** Ready to begin Phase 2 — Machine Simulator.

Say **"Begin Phase 2"** to proceed.
