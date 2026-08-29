"""Machine operating conditions supported by the simulator."""

from __future__ import annotations

from enum import Enum


class MachineCondition(str, Enum):
    """Named scenarios that alter the simulated machine signal."""

    NORMAL = "normal"
    EXCESSIVE_VIBRATION = "excessive_vibration"
    IMBALANCE = "imbalance"
    MISALIGNMENT = "misalignment"
    BEARING_DEGRADATION = "bearing_degradation"
    TEMPERATURE_INCREASE = "temperature_increase"
    SUDDEN_EVENTS = "sudden_events"
    SENSOR_NOISE = "sensor_noise"

    @classmethod
    def parse(cls, value: str) -> "MachineCondition":
        """Parse a CLI/config value using spaces and hyphens as separators."""
        normalised = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "bearing": cls.BEARING_DEGRADATION,
            "temperature": cls.TEMPERATURE_INCREASE,
            "sudden_vibration_events": cls.SUDDEN_EVENTS,
            "sensor": cls.SENSOR_NOISE,
        }
        if normalised in aliases:
            return aliases[normalised]
        try:
            return cls(normalised)
        except ValueError as exc:
            choices = ", ".join(item.value for item in cls)
            raise ValueError(f"Unknown condition {value!r}; choose one of: {choices}") from exc


CONDITIONS = tuple(MachineCondition)
"""All supported conditions, in CLI display order."""
