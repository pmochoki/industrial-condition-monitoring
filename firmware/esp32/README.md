# ESP32 Firmware

Primary firmware target for the condition monitoring node.

**Status:** Not yet implemented — Phase 8.

## Target Board

ESP32-DevKitC (ESP32-WROOM-32) — see [docs/hardware.md](../../docs/hardware.md).

## Build System

PlatformIO or ESP-IDF (decision deferred to Phase 8).

## TODO (Phase 8)

- [ ] Project skeleton with build configuration
- [ ] Accelerometer driver (ADXL345)
- [ ] Temperature driver (DS18B20)
- [ ] Timer-driven sampling at 2048 Hz
- [ ] CMSIS-DSP filter and FFT
- [ ] Anomaly detection (ported from Python)
- [ ] MQTT client with LWT
- [ ] NVS configuration
