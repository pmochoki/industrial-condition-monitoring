"""Contracts shared by simulator, edge processing, and future firmware."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class RawSampleWindowLike(Protocol):
    """Minimum input contract required by the processing pipeline."""

    timestamp: datetime
    device_id: str
    sample_rate_hz: int
    ax_g: list[float]
    ay_g: list[float]
    az_g: list[float]
    temperature_c: float


@dataclass(frozen=True)
class FeatureVector:
    """Processed machine features published by the edge node."""

    timestamp: datetime
    device_id: str
    temperature_c: float
    vibration_x: float
    vibration_y: float
    vibration_z: float
    vibration_rms: float
    vibration_peak: float
    vibration_peak_to_peak: float
    vibration_std: float
    crest_factor: float
    dominant_frequency_hz: float
