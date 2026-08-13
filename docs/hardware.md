# Hardware Design

**Phase 1 — Design Specification**  
*Implementation: Phase 8*

---

## 1. Overview

The physical condition monitoring node is designed as a low-cost retrofit module attachable to legacy industrial machinery. It samples 3-axis vibration and temperature, performs edge processing, and publishes telemetry over WiFi/MQTT.

This document defines the target hardware architecture. **No firmware is implemented in Phase 1.**

---

## 2. Recommended Bill of Materials

| Component | Recommended Part | Interface | Est. Cost | Notes |
|-----------|-----------------|----------|-----------|-------|
| Microcontroller | ESP32-DevKitC (ESP32-WROOM-32) | — | ~$8 | Dual-core, WiFi/BLE, 520 KB SRAM |
| Accelerometer | ADXL345 or LIS3DH | I2C / SPI | ~$3 | ±16 g range, configurable ODR |
| Temperature | DS18B20 or TMP117 | 1-Wire / I2C | ~$2 | ±0.5 °C accuracy |
| Enclosure | IP54 project box | — | ~$5 | Ventilation for temperature sensor |
| Power | 5 V USB or 24 V DC-DC module | — | ~$5 | Industrial machines often have 24 V available |
| Cabling | Shielded 4-wire for sensors | — | ~$3 | Short runs (< 1 m) to reduce noise |
| Mounting | M4 bolt or magnetic base | — | — | Rigid coupling to bearing housing critical |

**Total estimated BOM:** ~$25–35 (excluding enclosure and industrial power supply)

---

## 3. Block Diagram

```
                    ┌─────────────────────────────────────┐
                    │           ESP32 Module              │
                    │                                     │
  ADXL345 ──I2C────▶│  Core 0: Sampling ISR              │
  (3-axis accel)    │    Timer → read → circular buffer   │
                    │                                     │
  DS18B20 ──1-Wire─▶│  Core 1: Processing + MQTT         │
  (temperature)     │    Filter → features → anomaly       │
                    │    → WiFi → MQTT publish             │
                    │                                     │
  5V/24V ──Power───▶│  Watchdog, NVS config, diagnostics │
                    └──────────────┬──────────────────────┘
                                   │ WiFi
                                   ▼
                              MQTT Broker
```

---

## 4. Sensor Selection Rationale

### 4.1 Accelerometer

**Primary:** ADXL345 (I2C/SPI, ±2/4/8/16 g, up to 3200 Hz ODR)  
**Alternative:** LIS3DH (I2C/SPI, ±2/4/8/16 g, up to 5.3 kHz ODR — preferred if 2048 Hz sampling confirmed achievable)

Selection criteria:
- 3-axis (capture axial and radial vibration)
- ODR ≥ 2048 Hz (verify with specific part and bus speed)
- I2C for wiring simplicity; SPI if I2C throughput insufficient
- ±16 g range covers most industrial machinery acceleration levels

**Mounting:** Adhesive or bolt mount to bearing housing or motor frame. Mounting orientation documented in config for axis mapping.

### 4.2 Temperature

**Primary:** DS18B20 (1-Wire, ±0.5 °C, waterproof probe available)  
**Alternative:** TMP117 (I2C, ±0.1 °C, shares bus with accelerometer)

Temperature sensor mounted near motor winding or bearing housing. Thermal contact (thermal paste or probe insertion) preferred over ambient air measurement.

---

## 5. Firmware Module Architecture

```
firmware/
├── esp32/
│   ├── main/
│   │   ├── main.cpp              # Entry point, task creation
│   │   └── config.h              # Compile-time defaults
│   ├── drivers/
│   │   ├── accelerometer.h       # Abstract interface
│   │   ├── adxl345.cpp           # ADXL345 implementation
│   │   ├── temperature.h         # Abstract interface
│   │   └── ds18b20.cpp           # DS18B20 implementation
│   ├── dsp/
│   │   ├── filter.cpp            # Pre-computed biquad coefficients
│   │   ├── features.cpp          # RMS, peak, crest factor
│   │   └── fft.cpp               # CMSIS-DSP wrapper
│   ├── anomaly/
│   │   ├── thresholds.cpp        # Ported from Python reference
│   │   └── baseline.cpp          # Rolling baseline tracker
│   ├── mqtt/
│   │   ├── client.cpp            # Connection, publish, LWT
│   │   └── serializer.cpp        # JSON payload construction
│   ├── config/
│   │   └── nvs_config.cpp        # NVS read/write for device ID, broker
│   └── diagnostics/
│       ├── watchdog.cpp
│       └── error_log.cpp
└── stm32/
    └── README.md                 # Alternative target (Phase 8+)
```

### Driver Abstraction

```cpp
class Accelerometer {
public:
    virtual bool init() = 0;
    virtual bool readSample(AxisData& out) = 0;
    virtual uint32_t getODR() const = 0;
    virtual ~Accelerometer() = default;
};
```

Allows swapping ADXL345 ↔ LIS3DH without changing application logic.

---

## 6. Sampling on ESP32

### Timer-Driven Acquisition

- **Hardware timer** triggers sampling ISR at 2048 Hz
- ISR reads accelerometer via I2C (or DMA if SPI) and writes to lock-free circular buffer
- Processing task on Core 1 consumes filled windows from buffer

### I2C Throughput Concern

ADXL345 I2C read at 400 kHz: ~6 bytes × overhead ≈ 200 µs per read. At 2048 Hz (488 µs period), I2C is feasible with fast mode (400 kHz). If insufficient, switch to SPI (~10× faster).

**Action item for Phase 8:** Benchmark actual read latency before committing to I2C.

---

## 7. Power

| Source | Condition | Solution |
|--------|-----------|----------|
| Bench development | USB 5 V | DevKit USB port |
| Industrial retrofit | 24 V DC available | LM2596 or TRACO DC-DC to 5 V/3.3 V |
| Battery (temporary) | No wired power | 18650 + TP4056 (limited runtime, demo only) |

Reverse polarity protection and TVS diode recommended for industrial 24 V input.

---

## 8. STM32 Alternative

If STM32 is preferred:

- Use **STM32F4** or **STM32H7** for CMSIS-DSP performance
- Add **ESP8266 or ESP32 as WiFi coprocessor** for MQTT (AT firmware or custom SPI bridge)
- Better deterministic sampling timing
- Higher BOM and integration complexity

The `firmware/stm32/` directory is reserved for this target. Shared algorithm code (filter coefficients, threshold logic) will be in a common header-only library where possible.

---

## 9. Hardware vs Simulator Swap

Both implement the same `MachineDataSource` contract:

| Aspect | Simulator | Hardware |
|--------|-----------|----------|
| Data origin | Physics-informed models | I2C/SPI sensor reads |
| Sample rate | Exact 2048 Hz | Timer-driven, measured |
| Temperature | Modelled drift | DS18B20 read |
| MQTT source field | `"simulator"` | `"hardware"` |
| Noise | Configurable synthetic | Sensor + electrical noise |

The backend and dashboard require no changes when swapping sources.

---

## 10. Safety Disclaimer

This node is a **monitoring and demonstration device**, not a safety instrumented system (SIS). It must not be used as the sole basis for emergency machine shutdown without independent safety verification.

---

## 11. Related Documents

- [Architecture](architecture.md)
- [Signal Processing](signal-processing.md)
- [Engineering Decisions — ED-02, ED-03](engineering-decisions.md)
