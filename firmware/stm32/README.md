# STM32 Firmware (Alternative Target)

Alternative firmware target for applications requiring better real-time determinism.

**Status:** Not planned until ESP32 target is complete — Phase 8+.

## Approach

- STM32F4 or STM32H7 for CMSIS-DSP performance
- External WiFi module (ESP8266/ESP32 coprocessor) for MQTT
- Shared algorithm headers with ESP32 target where possible

See [docs/hardware.md](../../docs/hardware.md) — Section 8.
