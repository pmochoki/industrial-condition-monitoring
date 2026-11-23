# Edge Signal Processing, Fault Detection & MQTT

Python reference implementation of the edge pipeline, designed to be portable to ESP32 firmware.

**Status:** Phases 3, 4, and 5 are complete. The next planned work is Phase 6 — backend ingestion and storage.

## Implemented

- Signal processing: configurable Butterworth bandpass filtering, DC removal, resultant 3-axis vibration, time-domain features, and Hanning-windowed FFT.
- Fault detection: YAML-configured absolute thresholds, rolling z-score baseline, weighted composite score, and explainable NORMAL/WARNING/CRITICAL results. Simulated fault cases verify expected warning and critical escalations.
- MQTT: QoS 1 telemetry and transition alerts, retained online/offline status, Last Will, TLS/auth environment options, and local Mosquitto Compose setup.

Run the complete suite with `python -m pytest -q` (34 tests). For the local demo, start Mosquitto using `docker compose -f docker/docker-compose.yml up -d`, subscribe with `mosquitto_sub -h localhost -t 'machines/+/#' -v`, then run `python -m edge.mqtt_demo --condition excessive_vibration --severity 0.5 --windows 10`.

See [Fault Detection](../docs/fault-detection.md), [MQTT Architecture](../docs/mqtt-architecture.md), and [the roadmap](../docs/roadmap.md) for design and next steps.
