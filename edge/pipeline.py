"""Orchestration of the Phase 3 edge signal-processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from edge.features.frequency_domain import dominant_frequency_hz
from edge.features.time_domain import as_resultant, compute_time_domain_features
from edge.filtering.butterworth import bandpass_filter
from edge.filtering.detrend import remove_dc_offset
from edge.interfaces import FeatureVector, RawSampleWindowLike


@dataclass(frozen=True)
class ProcessingConfig:
    """Signal-processing settings matching config/default.yaml."""

    filter_enabled: bool = True
    low_cutoff_hz: float = 2.0
    high_cutoff_hz: float = 1000.0
    filter_order: int = 4
    dominant_min_frequency_hz: float = 2.0


class SignalProcessingPipeline:
    """Convert raw acceleration windows into dashboard-ready features."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        self.config = config or ProcessingConfig()

    def process(self, window: RawSampleWindowLike) -> FeatureVector:
        """Process one raw sample window."""
        axes = tuple(
            self._prepare_axis(axis, window.sample_rate_hz)
            for axis in (window.ax_g, window.ay_g, window.az_g)
        )
        resultant = as_resultant(*axes)
        time_features = compute_time_domain_features(resultant)
        dominant_frequency = dominant_frequency_hz(
            resultant,
            window.sample_rate_hz,
            min_frequency_hz=self.config.dominant_min_frequency_hz,
        )
        return FeatureVector(
            timestamp=window.timestamp,
            device_id=window.device_id,
            temperature_c=float(window.temperature_c),
            vibration_x=float(np.mean(axes[0])),
            vibration_y=float(np.mean(axes[1])),
            vibration_z=float(np.mean(axes[2])),
            vibration_rms=time_features.rms,
            vibration_peak=time_features.peak,
            vibration_peak_to_peak=time_features.peak_to_peak,
            vibration_std=time_features.std_dev,
            crest_factor=time_features.crest_factor,
            dominant_frequency_hz=dominant_frequency,
        )

    def _prepare_axis(self, samples: list[float], sample_rate_hz: int) -> np.ndarray:
        if self.config.filter_enabled:
            return bandpass_filter(
                samples,
                sample_rate_hz=sample_rate_hz,
                low_cutoff_hz=self.config.low_cutoff_hz,
                high_cutoff_hz=self.config.high_cutoff_hz,
                order=self.config.filter_order,
            )
        return remove_dc_offset(samples)
