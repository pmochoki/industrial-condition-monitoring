# Firmware

ESP32 and STM32 firmware for the physical condition monitoring node.

**Status:** Not yet implemented — begins in Phase 8.

## Targets

| Directory | Platform | Status |
|-----------|----------|--------|
| `esp32/` | ESP32 (primary) | Phase 8 |
| `stm32/` | STM32 (alternative) | Phase 8+ |

## Design

Firmware modules mirror the Python edge processing architecture:

- Sensor drivers (abstract interface)
- Timer-driven sampling
- DSP (filter, features, FFT via CMSIS-DSP)
- Anomaly detection (ported from Python reference)
- MQTT publishing with LWT
- NVS configuration storage

See [docs/hardware.md](../docs/hardware.md) for BOM and block diagram.
