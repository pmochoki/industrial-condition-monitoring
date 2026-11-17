# Edge Signal Processing & Anomaly Detection

Python reference implementation of the edge processing modules, designed to be portable to ESP32 firmware.

**Status:** Phase 3 signal processing is complete. Phase 4 anomaly detection is next.

## Phase 3 implemented

- Configurable 4th-order Butterworth bandpass filter and DC-offset removal
- Resultant 3-axis acceleration and time-domain features: mean, RMS, peak, peak-to-peak, standard deviation, and crest factor
- Hanning-windowed FFT and dominant-frequency extraction
- SignalProcessingPipeline maps a raw sample window to a FeatureVector while preserving device, timestamp, and temperature metadata

Run the full suite with: python -m pytest -q. The current suite has 14 passing tests across simulator and signal-processing behavior.

See [docs/signal-processing.md](../docs/signal-processing.md) for design details and [docs/roadmap.md](../docs/roadmap.md) for the next phases.
