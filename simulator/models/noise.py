"""Deterministic sensor noise primitives for simulated measurements."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class NoiseModel:
    """Gaussian noise settings expressed in engineering units."""

    vibration_std_g: float = 0.002
    temperature_std_c: float = 0.05

    def vibration(self, rng: random.Random, multiplier: float = 1.0) -> float:
        """Return one acceleration noise sample in g."""
        return rng.gauss(0.0, self.vibration_std_g * multiplier)

    def temperature(self, rng: random.Random) -> float:
        """Return one temperature noise sample in degrees Celsius."""
        return rng.gauss(0.0, self.temperature_std_c)
