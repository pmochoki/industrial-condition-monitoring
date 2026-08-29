# Phase 2 — Machine Simulator

Generates physics-informed synthetic vibration and temperature signals for defined machine conditions.

**Status:** Implemented — Phase 2 artifact added; run the test suite locally to verify.

## Structure

```
simulator/
├── __init__.py
├── models/
│   ├── machine.py        # Base rotating machine model
│   ├── faults.py         # Fault condition generators
│   └── noise.py          # Sensor noise models
├── conditions.py           # Condition enum and severity control
├── source.py               # MachineDataSource implementation
└── cli.py                  # Command-line interface
```

## Fault Conditions

- normal — baseline rotating signal
- excessive_vibration — elevated 1× energy and noise
- imbalance — elevated 1× shaft-frequency energy
- misalignment — elevated 2× and 3× harmonics
- bearing_degradation — high-frequency content and periodic impulses
- temperature_increase — temperature drift over time
- sudden_events — intermittent high-amplitude impulses
- sensor_noise — elevated measurement noise

## Usage

Generate 1024 CSV samples to stdout:

    python -m simulator --condition imbalance --severity 0.5

Write JSON samples to a file:

    python -m simulator --condition bearing_degradation --severity 0.8 --format json --output bearing.json

All conditions accept a configurable severity from 0.0 to 1.0. Use --seed for reproducible signals; the default seed is 42. The generated RawSampleWindow implements the MachineDataSource contract described in [architecture.md](../docs/architecture.md).

See [docs/roadmap.md](../docs/roadmap.md) for the remaining Phase 2 verification step.
