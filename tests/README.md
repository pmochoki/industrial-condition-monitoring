# Tests

Unit and integration tests for all project phases.

**Status:** Phase 2 simulator and Phase 3 signal-processing tests are implemented; all 14 currently pass.

## Current tests

- tests/test_simulator.py — deterministic output, fault behavior, temperature drift, and CLI output
- tests/test_signal_processing.py — resultant signals, time-domain features, FFT, filter response, DC removal, and pipeline integration

Run from the repository root:

    python -m pytest -q

See [docs/roadmap.md](../docs/roadmap.md) for upcoming integration and end-to-end tests.
