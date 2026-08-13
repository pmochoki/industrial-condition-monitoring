# Edge Signal Processing & Anomaly Detection

Reference implementation of edge processing modules. Validated in Python, then ported to ESP32 firmware.

**Status:** Not yet implemented — begins in Phase 3 (signal processing) and Phase 4 (anomaly detection).

## Planned Structure

```
edge/
├── interfaces.py           # MachineDataSource, FeatureVector, AnomalyScorer
├── sampling/               # Buffer management, windowing
├── filtering/              # Butterworth bandpass, detrend
├── features/
│   ├── time_domain.py      # RMS, peak, crest factor
│   └── frequency_domain.py # FFT, dominant frequency
├── anomaly/
│   ├── thresholds.py       # Absolute limit checking
│   ├── baseline.py         # Rolling baseline, z-score
│   └── scorer.py           # Composite score, status classification
├── mqtt/                   # Telemetry publisher (Phase 5)
└── pipeline.py             # Full processing orchestrator
```

See [docs/signal-processing.md](../docs/signal-processing.md) and [docs/fault-detection.md](../docs/fault-detection.md).
