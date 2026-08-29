"""Butterworth bandpass filtering for vibration windows."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt

from edge.filtering.detrend import remove_dc_offset


def bandpass_filter(
    samples: np.ndarray | list[float],
    sample_rate_hz: float,
    low_cutoff_hz: float = 2.0,
    high_cutoff_hz: float = 1000.0,
    order: int = 4,
) -> np.ndarray:
    """Apply a zero-phase Butterworth bandpass filter to one axis."""
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("samples must be a non-empty one-dimensional sequence")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    if order <= 0:
        raise ValueError("order must be positive")
    nyquist_hz = sample_rate_hz / 2.0
    if not 0.0 < low_cutoff_hz < high_cutoff_hz < nyquist_hz:
        raise ValueError("cutoffs must satisfy 0 < low < high < Nyquist")
    if values.size < 32:
        raise ValueError("at least 32 samples are required for stable filtering")

    centred = remove_dc_offset(values)
    sos = butter(
        order,
        [low_cutoff_hz / nyquist_hz, high_cutoff_hz / nyquist_hz],
        btype="bandpass",
        output="sos",
    )
    return sosfiltfilt(sos, centred)
