# Signal Processing

**Phase 1 — Design Specification**  
*Implementation: Phase 3*

---

## 1. Purpose

Extract meaningful condition indicators from raw 3-axis acceleration and temperature data at the edge node. The processing pipeline must be modular, testable, and portable from Python (reference) to ESP32 firmware (C++).

---

## 2. Pipeline Overview

```
Raw acceleration samples (ax, ay, az) × N
    │
    ▼
┌─────────────────┐
│  Pre-processing │  Remove DC offset, optional detrend
└────────┬────────┘
         ▼
┌─────────────────┐
│  Bandpass filter│  Butterworth, configurable cutoffs
└────────┬────────┘
         ▼
┌─────────────────┐
│ Time-domain     │  mean, RMS, peak, peak-to-peak,
│ features        │  std dev, crest factor
└────────┬────────┘
         ▼
┌─────────────────┐
│ Frequency-domain│  FFT → magnitude spectrum →
│ analysis        │  dominant frequency, harmonic peaks
└────────┬────────┘
         ▼
    FeatureVector
```

Temperature is read independently at a lower rate (default 1 Hz) and attached to the feature vector at publish time.

---

## 3. Sampling Parameters

| Parameter | Default | Engineering Basis |
|-----------|---------|-------------------|
| Sample rate | 2048 Hz | See ED-04 in [engineering-decisions.md](engineering-decisions.md) |
| Window size | 1024 samples | 0.5 s at 2048 Hz; power-of-2 for radix-2 FFT |
| Overlap | 50% | Improves temporal resolution of feature updates |
| Publish rate | 1 Hz | One feature vector per second (aggregated from overlapping windows) |
| Temperature rate | 1 Hz | Thermal time constants are slow; 1 Hz is sufficient |

### Nyquist and Frequency Resolution

- **Nyquist limit:** 1024 Hz — any frequency content above this will alias
- **Frequency bin width:** 2048 / 1024 = **2 Hz per bin**
- **Shaft speed example:** 1200 RPM = 20 Hz → fundamental appears in bin 10

### What This Configuration Can Detect

| Condition | Detectable? | Mechanism |
|-----------|-------------|-----------|
| Imbalance | Yes | Elevated 1× shaft frequency amplitude |
| Misalignment | Partially | 2× and 3× harmonic elevation |
| Looseness | Partially | Multiple harmonics + elevated crest factor |
| Bearing degradation (advanced) | Limited | High-frequency impulses may be attenuated by filter/MEMS response |
| Overheating | Yes (temperature) | Direct temperature trend |
| Sudden impact | Yes | Peak and crest factor spike |

### What This Configuration Cannot Reliably Detect

- Early bearing inner/outer race defects (requires envelope analysis, typically 5–40 kHz range)
- Gear mesh frequencies on high-speed gearboxes
- Sub-Hz structural vibration (blocked by high-pass filter)

**These limitations are intentional and documented — not hidden.**

---

## 4. Filtering

### 4.1 Bandpass Filter

- **Type:** Butterworth (maximally flat passband)
- **Order:** 4
- **Low cutoff:** 2 Hz — removes DC drift, thermal effects, and building vibration
- **High cutoff:** 1000 Hz — below Nyquist; prevents amplification of sensor noise near Nyquist

### 4.2 Anti-Aliasing

On hardware, the accelerometer's internal ODR (output data rate) acts as the first anti-aliasing stage. The configured ODR must be ≥ sample rate. Software filter provides additional rolloff.

On the simulator, signals are generated band-limited to the Nyquist frequency.

---

## 5. Time-Domain Features

All features computed on the **resultant vibration** unless otherwise noted:

```
a_resultant(t) = sqrt(ax(t)² + ay(t)² + az(t)²)
```

| Feature | Formula | Unit | Purpose |
|---------|---------|------|---------|
| Mean | (1/N) Σ x | g | DC offset check (should be ~0 after filtering) |
| RMS | sqrt((1/N) Σ x²) | g | Overall vibration severity (ISO 10816 uses velocity RMS; we use acceleration for MEMS) |
| Peak | max(\|x\|) | g | Maximum instantaneous amplitude |
| Peak-to-peak | max(x) − min(x) | g | Total excursion range |
| Std dev | sqrt((1/N) Σ (x − mean)²) | g | Signal variability |
| Crest factor | peak / RMS | dimensionless | Impulsiveness indicator (> 3 typical for bearing defects) |

Individual axis values (vibration_x/y/z) published as window mean for dashboard display.

---

## 6. Frequency-Domain Analysis

### 6.1 FFT

- **Input:** 1024 filtered samples (Hanning window applied to reduce spectral leakage)
- **Output:** Single-sided magnitude spectrum (512 bins)
- **Dominant frequency:** Bin with maximum magnitude above the high-pass cutoff

### 6.2 Harmonic Analysis (Future Enhancement)

Phase 3 implements dominant frequency only. Phase 10+ may add:
- 1×, 2×, 3× shaft speed harmonic amplitudes
- Sideband detection around shaft frequency

---

## 7. Module Structure (Planned)

```
edge/
├── __init__.py
├── interfaces.py          # MachineDataSource, FeatureVector protocols
├── sampling/
│   ├── buffer.py          # Circular sample buffer
│   └── window.py          # Window extraction with overlap
├── filtering/
│   ├── butterworth.py     # Bandpass filter design and apply
│   └── detrend.py         # DC removal
├── features/
│   ├── time_domain.py     # RMS, peak, crest factor, etc.
│   └── frequency_domain.py # FFT, dominant frequency
└── pipeline.py            # Orchestrates full processing chain
```

---

## 8. Validation Strategy (Phase 3)

Unit tests with known synthetic inputs:

| Test | Input | Expected Output |
|------|-------|-----------------|
| RMS sine wave | 1 g amplitude sine at 50 Hz | RMS ≈ 0.707 g |
| Crest factor sine | Pure sine | Crest factor ≈ 1.414 |
| Dominant frequency | 20 Hz sine at 2048 Hz | Dominant = 20 Hz ± 2 Hz |
| Filter rejection | 0.5 Hz + 50 Hz input | 0.5 Hz attenuated, 50 Hz passed |
| DC removal | Constant offset + sine | Mean ≈ 0 after processing |

---

## 9. Firmware Porting Notes (Phase 8)

| Python | ESP32 Equivalent |
|--------|-----------------|
| `scipy.signal.butter` | CMSIS-DSP biquad cascade or pre-computed coefficients |
| `numpy.fft.rfft` | CMSIS-DSP `arm_rfft_fast_f32` |
| Float64 | Float32 (sufficient for demo precision) |

Filter coefficients will be pre-computed offline and stored as constants in firmware — not designed at runtime.

---

## 10. Assumptions

1. Machine vibration is predominantly periodic (rotating equipment)
2. Sensor is rigidly mounted to bearing housing or motor frame
3. Single operating speed or speed variation is slow relative to window duration
4. Ambient temperature changes are gradual
5. Sensor noise floor is stationary

---

## 11. Related Documents

- [Architecture](architecture.md)
- [Fault Detection](fault-detection.md)
- [Limitations](limitations.md)
