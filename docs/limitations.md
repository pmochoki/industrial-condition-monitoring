# Limitations & Assumptions

An honest assessment of what this system can and cannot do. Portfolio projects lose credibility when limitations are hidden.

---

## 1. Sensor Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| MEMS accelerometer dynamic range (~±16 g) | Saturation on high-impact machinery | Select appropriate range; document mounting |
| MEMS frequency response rolls off above ~1 kHz | Misses high-frequency bearing defect signatures | Document; recommend IEPE for production |
| I2C bus jitter at 2048 Hz | Sample timing not perfectly uniform | SPI alternative; timestamp interpolation |
| Single sensor location | Cannot localize fault to specific bearing | Multi-node expansion documented as future work |
| Temperature sensor placement | Air vs contact measurement differs significantly | Document mounting requirement |

---

## 2. Signal Processing Limitations

| Limitation | Impact |
|------------|--------|
| 2048 Hz sample rate | Nyquist limit 1024 Hz — insufficient for envelope demodulation of bearing defects (typically 2–6 kHz carrier) |
| 1024-sample window (0.5 s) | Frequency resolution 2 Hz — may merge close harmonics |
| No order tracking | Speed variation smears spectral peaks |
| No envelope analysis | Cannot detect early bearing inner/outer race faults |
| Acceleration RMS vs velocity RMS | ISO 10816 zones are in velocity; direct comparison requires integration (not implemented) |
| Simplified filter design | Fixed bandpass — no adaptive filtering for changing conditions |

---

## 3. Anomaly Detection Limitations

| Limitation | Impact |
|------------|--------|
| Threshold-based only | Requires per-machine calibration; no automatic adaptation |
| No fault classification | Detects severity, not fault type (imbalance vs bearing) |
| Baseline warm-up required | 60 windows (~60 s) before z-score detection active |
| Stationary speed assumption | Variable-speed machines need order tracking (not implemented) |
| No multi-sensor fusion | Single node, single viewpoint |
| Simulator-trained thresholds | Real machine thresholds will differ — manual calibration required |

---

## 4. System Architecture Limitations

| Limitation | Impact |
|------------|--------|
| SQLite database | Single-writer; not suitable for fleet-scale deployment |
| Local Mosquitto broker | No cloud redundancy; single point of failure |
| No authentication (dev mode) | Not production-secure without TLS + credentials |
| No OTA firmware updates | Physical access required for firmware changes |
| WiFi dependency (ESP32) | Unreliable in industrial RF environments without planning |
| No redundant nodes | Single sensor failure = blind spot |

---

## 5. Simulator Limitations

| Limitation | Impact |
|------------|--------|
| Physics-informed, not physics-exact | Simplified harmonic models; real machines are more complex |
| Single shaft speed per scenario | No speed ramping or load variation |
| No structural resonance modelling | Resonance amplification not simulated |
| Labelled as simulated | Must not be presented as real machine data |

---

## 6. What This System IS

- A **portfolio demonstration** of end-to-end condition monitoring engineering
- A **development platform** for testing signal processing and detection algorithms
- A **reference architecture** for low-cost industrial IoT retrofit
- An **explainable monitoring system** with documented thresholds and feature-level alerts

## 7. What This System IS NOT

- A certified vibration analysis instrument (no ISO 17025 calibration)
- A replacement for industrial CMS platforms (SKF @ptitude, Emerson AMS, etc.)
- A safety instrumented system (SIL-rated shutdown)
- A production-ready product without further hardening
- An ML/AI system (Phase 4 uses explainable thresholds only)

---

## 8. Recommended Future Improvements

Priority-ordered for production hardening:

1. **Envelope demodulation** — bearing fault frequency detection
2. **Order tracking** — speed-normalised spectral analysis
3. **Velocity integration** — ISO 10816 zone compliance
4. **Multi-node fleet management** — PostgreSQL/TimescaleDB backend
5. **ML anomaly scorer** — Isolation Forest with SHAP explanations
6. **TLS + MQTT authentication** — production security
7. **OTA firmware updates** — ESP32 HTTPS OTA
8. **IEPE sensor support** — industrial-grade vibration measurement
9. **Edge buffering** — store-and-forward on connectivity loss
10. **IEC 62443 compliance** — industrial cybersecurity standard

---

## 9. Assumptions

1. Target machinery: low-to-medium speed rotating equipment (600–3600 RPM)
2. Operating environment: indoor industrial, -10 to +50 °C ambient
3. Power available: 5 V USB (dev) or 24 V DC (industrial retrofit)
4. Network: WiFi available within range of ESP32
5. Operator: engineering-literate user who can interpret vibration trends
6. Maintenance context: thresholds tuned during commissioning with known-good baseline

---

## 10. Related Documents

- [Engineering Decisions](engineering-decisions.md)
- [Signal Processing](signal-processing.md)
- [Hardware Design](hardware.md)
