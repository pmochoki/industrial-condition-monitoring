# Tests

Unit and integration tests for the simulator and edge pipeline.

**Status:** Phases 2–5 have 34 passing tests. The Phase 4 cases cover every simulator fault type, status escalation, and explanation rules; Phase 5 covers MQTT payloads, QoS/retain behavior, alerts, and offline status.

## Test modules

- `tests/test_simulator.py` — deterministic output, fault behavior, temperature drift, and CLI output.
- `tests/test_signal_processing.py` — resultant signals, time-domain features, FFT, filter response, DC removal, and pipeline integration.
- `tests/test_anomaly.py` — thresholds, rolling baseline, composite scoring, and all simulated fault outcomes.
- `tests/test_mqtt.py` — message schema, QoS/retain flags, transition alerts, connection status, and graceful shutdown.

Run from the repository root:

    python -m pytest -q

See [the roadmap](../docs/roadmap.md) for Phase 6 backend integration and later end-to-end tests.
