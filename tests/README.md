# Tests

Unit and integration tests for all project phases.

**Status:** Test implementation begins in Phase 3.

## Planned Structure

```
tests/
├── unit/
│   ├── test_filtering.py       # Phase 3
│   ├── test_features.py        # Phase 3
│   ├── test_anomaly.py         # Phase 4
│   └── test_simulator.py       # Phase 2
├── integration/
│   ├── test_mqtt_pipeline.py   # Phase 5
│   └── test_backend_api.py     # Phase 6
└── e2e/
    └── test_full_pipeline.py   # Phase 9
```

Run tests (when implemented):

```bash
pytest
```
