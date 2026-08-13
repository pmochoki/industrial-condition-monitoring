# Phase 2 — Machine Simulator

Generates physics-informed synthetic vibration and temperature signals for defined machine conditions.

**Status:** Not yet implemented — begins in Phase 2.

## Planned Structure

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

## Fault Conditions (Planned)

- Normal operation
- Excessive vibration
- Imbalance
- Misalignment
- Bearing degradation
- Temperature increase
- Sudden vibration events
- Sensor noise

See [docs/roadmap.md](../docs/roadmap.md) for Phase 2 deliverables.
