# Fault Detection & Anomaly Scoring

**Phase 1 — Design Specification**  
*Implementation: Phase 4*

---

## 1. Design Philosophy

Fault detection must be **explainable**. Every status classification (NORMAL, WARNING, CRITICAL) must be traceable to specific feature values, thresholds, and rules — not an opaque model score.

Machine learning may be added later via a pluggable `AnomalyScorer` interface without rewriting the pipeline.

---

## 2. Status Levels

| Status | Meaning | Typical Response |
|--------|---------|-----------------|
| **NORMAL** | All features within limits; anomaly score below warning | Continue monitoring |
| **WARNING** | One or more features exceed warning thresholds or statistical deviation | Investigate at next maintenance window |
| **CRITICAL** | Severe threshold breach or multiple concurrent warnings | Stop machine if safe; immediate inspection |

Status is the **worst case** across all evaluated rules (max severity wins).

---

## 3. Detection Methods

### 3.1 Absolute Threshold Checking

Each feature has configurable warning and critical limits in `config/thresholds.yaml`:

```
if vibration_rms > critical_threshold  → CRITICAL
elif vibration_rms > warning_threshold → WARNING
```

Thresholds are **per machine** — not hardcoded in source code.

Reference: ISO 10816 provides velocity RMS zones for machine classes. This project uses acceleration RMS from MEMS sensors — thresholds are calibrated against the simulator's known-good baseline, not copied directly from ISO tables.

### 3.2 Baseline Deviation (Z-Score)

After a warm-up period (`baseline_warmup_windows`, default 60), the system maintains a rolling baseline (mean and std dev) for each feature.

```
z = (current_value - baseline_mean) / baseline_std

if |z| > z_score_critical → CRITICAL
elif |z| > z_score_warning → WARNING
```

Useful for detecting gradual degradation (bearing wear, temperature drift) before absolute limits are reached.

### 3.3 Composite Anomaly Score

A weighted combination of normalised feature deviations produces a single score (0.0–1.0):

```
score = Σ (weight_i × normalised_deviation_i)
```

Weights configured in `config/default.yaml` under `anomaly_detection.feature_weights`.

Normalisation maps each feature's deviation to 0.0–1.0 relative to its warning threshold.

| Score Range | Status |
|-------------|--------|
| 0.0 – 0.44 | NORMAL |
| 0.45 – 0.74 | WARNING |
| 0.75 – 1.0 | CRITICAL |

Thresholds configurable in `config/thresholds.example.yaml`.

### 3.4 Rule Engine Output

Each evaluation produces a list of triggered rules:

```python
triggered_rules = [
    "vibration_rms_g > warning (0.14 > 0.12)",
    "z_score_temperature > warning (2.3)",
]
```

These are included in telemetry and alert messages for dashboard display.

---

## 4. Architecture

```
FeatureVector
    │
    ▼
┌───────────────────┐
│ ThresholdChecker  │──▶ rule_results[]
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ BaselineTracker   │──▶ z_score_results[]
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ CompositeScorer   │──▶ anomaly_score
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ StatusClassifier  │──▶ AnomalyResult
└───────────────────┘
```

### Pluggable Scorer Interface

```python
class AnomalyScorer(Protocol):
    def score(self, features: FeatureVector) -> AnomalyResult: ...

class ThresholdScorer:
    """Phase 4 implementation — threshold + z-score + composite."""

class MLScorer:
    """Future — implements same interface."""
    pass  # TODO: Phase 10+
```

---

## 5. Machine Conditions vs Detection Response

Expected detection behaviour when tested against the Phase 2 simulator:

| Simulated Condition | Expected Feature Changes | Expected Status |
|--------------------|--------------------------|-----------------|
| Normal | Stable RMS, crest ~1.4–3.0, temp stable | NORMAL |
| Excessive vibration | High RMS and peak across all axes | WARNING → CRITICAL |
| Imbalance | Elevated 1× dominant frequency, moderate RMS increase | WARNING |
| Misalignment | 2×/3× harmonic elevation, axial vibration increase | WARNING |
| Bearing degradation | Increased crest factor, HF noise, impulse peaks | WARNING |
| Temperature increase | Gradual temp rise, possibly correlated RMS increase | WARNING → CRITICAL |
| Sudden vibration event | Transient peak and crest factor spike | WARNING (may self-clear) |
| Sensor noise | Elevated std dev without structured harmonic change | WARNING (if excessive) |

Automated tests in Phase 4 will verify these responses against configured thresholds.

---

## 6. Alert Generation

Alerts are generated on **status transitions only**:

```python
if new_status != previous_status:
    publish_alert(AlertMessage(...))
```

This prevents alert flooding during sustained fault conditions while ensuring operators are notified when conditions change.

Alert deduplication in the backend (Phase 6) prevents duplicate alerts if the edge reconnects.

---

## 7. Configuration Reference

| Config file | Purpose |
|-------------|---------|
| `config/thresholds.yaml` | Absolute limits and z-score parameters |
| `config/default.yaml` | Feature weights, warm-up period, composite score thresholds |

See `config/thresholds.example.yaml` for the full schema.

---

## 8. Limitations

- Threshold-based detection requires per-machine calibration — generic defaults will false-alarm on some machines
- Z-score baselines assume stationary operating conditions during warm-up
- Cannot distinguish fault *type* (imbalance vs misalignment) — only severity classification
- No automatic threshold adaptation — manual or scheduled recalibration required

Future: fault classification via harmonic pattern matching or ML, implemented as additional scorer.

---

## 9. Related Documents

- [Signal Processing](signal-processing.md)
- [MQTT Architecture](mqtt-architecture.md)
- [Limitations](limitations.md)
