"""Fault-specific signal changes used by the machine model."""

from __future__ import annotations

from dataclasses import dataclass

from simulator.conditions import MachineCondition


@dataclass(frozen=True)
class FaultProfile:
    """Additive signal characteristics for one condition and severity."""

    vibration_1x_g: float = 0.0
    vibration_2x_g: float = 0.0
    vibration_3x_g: float = 0.0
    bearing_harmonic_g: float = 0.0
    impulse_amplitude_g: float = 0.0
    temperature_rise_c_per_second: float = 0.0
    noise_multiplier: float = 1.0
    impulse_interval_s: float = 0.0


def profile_for(condition: MachineCondition, severity: float) -> FaultProfile:
    """Build a scaled profile for a condition.

    The amplitudes are intentionally modest, portfolio-scale engineering values.
    Severity is always clamped by validation at the public simulator boundary.
    """
    if not 0.0 <= severity <= 1.0:
        raise ValueError("severity must be between 0.0 and 1.0")

    if condition is MachineCondition.EXCESSIVE_VIBRATION:
        return FaultProfile(vibration_1x_g=0.055 * severity, noise_multiplier=1.0 + 4.0 * severity)
    if condition is MachineCondition.IMBALANCE:
        return FaultProfile(vibration_1x_g=0.085 * severity)
    if condition is MachineCondition.MISALIGNMENT:
        return FaultProfile(vibration_2x_g=0.060 * severity, vibration_3x_g=0.030 * severity)
    if condition is MachineCondition.BEARING_DEGRADATION:
        return FaultProfile(
            bearing_harmonic_g=0.035 * severity,
            impulse_amplitude_g=0.180 * severity,
            impulse_interval_s=0.25,
        )
    if condition is MachineCondition.TEMPERATURE_INCREASE:
        return FaultProfile(temperature_rise_c_per_second=12.0 * severity)
    if condition is MachineCondition.SUDDEN_EVENTS:
        return FaultProfile(impulse_amplitude_g=0.350 * severity, impulse_interval_s=0.75)
    if condition is MachineCondition.SENSOR_NOISE:
        return FaultProfile(noise_multiplier=1.0 + 20.0 * severity)
    return FaultProfile()
