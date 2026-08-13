# Engineering Decisions

This document records major architectural and engineering choices for the Industrial Condition Monitoring Node. Each decision follows the format: **Recommendation → Rationale → Alternatives → Trade-offs**.

---

## ED-01: Primary Development Language — Python

**Recommendation:** Use Python for the simulator, reference edge processing, backend, and tests.

**Rationale:**
- NumPy and SciPy provide validated implementations of filtering, FFT, and statistical operations
- Single language across the development pipeline reduces context switching
- Fast iteration for a portfolio project with incremental phases
- Firmware will be C/C++ on the microcontroller — Python serves as the reference implementation to validate algorithms before porting

**Alternatives considered:**
- **All C/C++** — closer to production edge code but slows Phases 2–7 significantly
- **Node.js backend** — good for I/O but weak for signal processing
- **Julia** — excellent numerics but smaller ecosystem and less portfolio recognition

**Trade-offs:**
- Python edge code is not deployable on the MCU — must be ported to firmware (Phase 8)
- GIL limits true parallel sampling simulation; acceptable for demo throughput

---

## ED-02: Microcontroller — ESP32 Primary, STM32 Secondary

**Recommendation:** Target **ESP32** as the primary firmware platform; document STM32 as an alternative.

**Rationale:**
- Built-in WiFi eliminates external communication module cost and complexity
- Dual-core architecture allows sampling on one core and MQTT on another
- Mature Arduino and ESP-IDF ecosystems with MQTT client libraries
- Common in IoT retrofit projects — realistic for a low-cost portfolio build

**Alternatives considered:**
- **STM32 + ESP8266/ESP32 as coprocessor** — better real-time determinism on STM32 but higher BOM and integration effort
- **Raspberry Pi** — not appropriate for embedded edge node (power, cost, reliability)

**Trade-offs:**
- ESP32 ADC and timing are less precise than dedicated STM32 + external ADC
- WiFi stack adds jitter to sampling — mitigated by timer-driven ISR acquisition with buffered transfer
- For hard safety-critical applications, STM32 would be preferred

**Note:** If you have existing STM32 hardware or strong preference, the firmware directory structure supports both targets with shared algorithm modules.

---

## ED-03: Vibration Sensor — MEMS Accelerometer

**Recommendation:** 3-axis MEMS accelerometer (e.g. ADXL345, MPU6050, or LIS3DH) for the portfolio build.

**Rationale:**
- Low cost (< $5), I2C/SPI interface, adequate for demonstration
- Sufficient for detecting gross faults (imbalance, misalignment, looseness) on low-to-medium speed machinery
- Easy to integrate with ESP32

**Alternatives considered:**
- **IEPE accelerometer + charge amplifier** — industrial standard, $100–500+, requires analog front-end
- **Piezo vibration sensor (analog)** — cheap but single-axis, no DC response, poor for low-frequency

**Trade-offs:**
- MEMS sensors have limited dynamic range and frequency response compared to industrial accelerometers
- Mounting location and coupling dramatically affect readings — must be documented
- Cannot reliably detect early-stage bearing inner/outer race defects without envelope analysis at higher sample rates

---

## ED-04: Sampling Rate — 2048 Hz

**Recommendation:** Default sample rate of **2048 Hz** with 1024-sample FFT windows.

**Rationale:**
- Nyquist frequency = 1024 Hz — captures harmonics well above typical shaft speeds (e.g. 1200 RPM = 20 Hz fundamental, up to ~50× harmonic at 1000 Hz)
- 1024-point FFT at 2048 Hz = 0.5 s observation window — resolves 2 Hz frequency bins
- Power-of-2 window size for efficient FFT (CMSIS-DSP on ESP32)
- Achievable on ESP32 with I2C accelerometer at moderate ODR settings

**Alternatives considered:**
- **10 kHz+** — needed for bearing defect frequency analysis; exceeds MEMS + ESP32 I2C practical throughput
- **512 Hz** — lower CPU load but misses higher harmonics and bearing-related frequencies
- **Variable rate** — adds complexity without benefit for demo scope

**Trade-offs:**
- Insufficient for high-speed spindles (> 10,000 RPM) or envelope demodulation of bearing faults in the 2–6 kHz range
- I2C bus speed may limit actual achievable rate with some sensors — SPI preferred if rate becomes bottleneck

See [signal-processing.md](signal-processing.md) for full analysis.

---

## ED-05: Database — SQLite

**Recommendation:** SQLite for telemetry and alert storage.

**Rationale:**
- Zero infrastructure — single file, no server process
- Reliable, well-tested, sufficient for single-node demo with thousands of records per day
- SQLAlchemy ORM allows future migration to PostgreSQL with minimal query changes
- Easy for portfolio reviewers to clone and run locally

**Alternatives considered:**
- **InfluxDB** — purpose-built for time-series; adds Docker dependency and learning curve
- **PostgreSQL + TimescaleDB** — production-grade but over-engineered for portfolio local demo
- **Flat files (CSV/Parquet)** — simple but poor query performance for dashboard history

**Trade-offs:**
- Write concurrency limited — one backend writer is fine for this use case
- No built-in downsampling/retention policies — implemented in application layer
- Not suitable for multi-site fleet management without migration

---

## ED-06: MQTT Broker — Eclipse Mosquitto

**Recommendation:** Mosquitto for local development and demonstration.

**Rationale:**
- De facto standard open-source MQTT broker
- Lightweight, runs in Docker or natively
- Supports QoS 0/1/2, retained messages, authentication
- Compatible with ESP32 MQTT clients (PubSubClient, ESP-IDF mqtt component)

**Alternatives considered:**
- **HiveMQ / EMQX** — enterprise features unnecessary for portfolio scope
- **AWS IoT Core / Azure IoT Hub** — cloud dependency, cost, complexity
- **Direct HTTP** — simpler but no pub/sub, no retained status, poor fit for IoT edge pattern

**Trade-offs:**
- Self-hosted broker requires Docker or local install
- No built-in persistence replay — backend must store history

---

## ED-07: Backend Framework — FastAPI

**Recommendation:** FastAPI with async MQTT subscriber and WebSocket support.

**Rationale:**
- Native async suits MQTT message handling and WebSocket dashboard push
- Automatic OpenAPI documentation — useful for portfolio
- Pydantic models align with JSON schema validation for telemetry
- Python ecosystem consistency with simulator and edge modules

**Alternatives considered:**
- **Flask + Flask-SocketIO** — synchronous default, less clean async MQTT integration
- **Go (Gin/Fiber)** — excellent performance but splits language from signal processing code

**Trade-offs:**
- Python backend is not the highest-throughput option — irrelevant at 1 Hz telemetry publish rates

---

## ED-08: Dashboard — React + TypeScript (Custom UI)

**Recommendation:** Custom React dashboard with an industrial monitoring aesthetic, not Grafana.

**Rationale:**
- Portfolio value: demonstrates full-stack capability including UI/UX design
- Grafana is powerful but hides frontend engineering from reviewers
- Custom UI allows feature-level alert explanations tailored to this project's anomaly model
- TypeScript provides type safety for telemetry schemas

**Alternatives considered:**
- **Grafana + InfluxDB** — fast to stand up but mostly configuration, not engineering
- **Streamlit** — Python-only, limited real-time WebSocket UX, looks like a data science demo
- **Vue/Svelte** — viable; React chosen for ecosystem size and charting library availability

**Trade-offs:**
- More development effort than Grafana
- Must implement charting, layout, and real-time updates manually (Recharts + WebSocket)

---

## ED-09: Anomaly Detection — Threshold + Statistical Baseline First

**Recommendation:** Explainable threshold and z-score based detection for Phase 4. Pluggable scorer interface for future ML.

**Rationale:**
- Thresholds are industry-standard for condition monitoring alarm limits (ISO 10816 references velocity/RMS zones)
- Explainable: each alert cites which feature exceeded which limit
- No training data required — works immediately with simulator
- Appropriate for portfolio demonstration of engineering judgment

**Alternatives considered:**
- **Isolation Forest / autoencoder** — requires labelled fault data; black-box without careful SHAP integration
- **Simple max-value alarm only** — too crude, misses gradual degradation trends
- **Cloud ML service** — dependency, cost, latency

**Trade-offs:**
- Less sensitive to subtle pattern changes that ML might catch
- Thresholds must be tuned per machine — documented in config, not hardcoded
- Baseline drift in changing operating conditions requires periodic recalibration

---

## ED-10: Simulator — Physics-Informed Models, Not Random Noise

**Recommendation:** Generate synthetic signals using superposition of harmonics, amplitude modulation, impulses, and noise models parameterised by fault type and severity.

**Rationale:**
- Validates that signal processing and detection actually respond to meaningful physical changes
- Demonstrates engineering understanding of vibration signatures
- Reproducible via configurable random seed
- Enables automated tests: "inject imbalance → expect dominant frequency peak at 1× shaft speed"

**Alternatives considered:**
- **Recorded real vibration data** — more realistic but not reproducible, licensing concerns, no controlled fault injection
- **Pure random walk** — useless for validating detection logic

**Trade-offs:**
- Synthetic models are approximations — real machines have more complex dynamics
- Must clearly label all simulator output as simulated in documentation and UI

---

## ED-11: Configuration — YAML + Environment Variables

**Recommendation:** Layered YAML config with `.env` for secrets and deployment overrides.

**Rationale:**
- YAML is human-readable for threshold tuning (important for automation engineers reviewing the repo)
- Environment variables standard for Docker deployment and CI
- Separates committed defaults from machine-specific thresholds (gitignored)

**Alternatives considered:**
- **JSON config** — less readable for nested threshold structures
- **TOML** — good alternative; YAML chosen for broader automation industry familiarity
- **Hardcoded constants** — rejected per project requirements

**Trade-offs:**
- Two config formats (YAML + .env) — documented precedence order in architecture.md

---

## Decisions Deferred to Later Phases

| Decision | Deferred to | Notes |
|----------|-------------|-------|
| ESP-IDF vs Arduino framework | Phase 8 | Depends on CMSIS-DSP needs and developer preference |
| Specific charting library | Phase 7 | Recharts vs uPlot — evaluate during dashboard build |
| Alert notification channel | Phase 6 | Webhook vs email — optional |
| Docker Compose service layout | Phase 5 | Depends on MQTT integration testing needs |

---

## Input Required From You

No blocking decisions at Phase 1. Optional preferences for Phase 8:

1. **ESP32 board preference** (e.g. ESP32-DevKitC, ESP32-WROOM) — affects pin mapping in firmware
2. **Specific accelerometer** if you already have hardware — otherwise ADXL345 or LIS3DH recommended

If no preference is stated, defaults in [hardware.md](hardware.md) will be used.
