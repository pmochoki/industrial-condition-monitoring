"""Frequency-domain analysis for processed vibration signals."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Spectrum:
    frequencies_hz: np.ndarray
    magnitudes: np.ndarray


def magnitude_spectrum(
    samples: np.ndarray | list[float],
    sample_rate_hz: float,
) -> Spectrum:
    """Return a single-sided, Hanning-windowed magnitude spectrum."""
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("samples must be a one-dimensional sequence with at least 2 values")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")

    window = np.hanning(values.size)
    windowed = (values - np.mean(values)) * window
    spectrum = np.fft.rfft(windowed)
    scale = 2.0 / np.sum(window) if np.sum(window) > 0.0 else 1.0
    magnitudes = np.abs(spectrum) * scale
    frequencies = np.fft.rfftfreq(values.size, d=1.0 / sample_rate_hz)
    return Spectrum(frequencies_hz=frequencies, magnitudes=magnitudes)


def dominant_frequency_hz(
    samples: np.ndarray | list[float],
    sample_rate_hz: float,
    min_frequency_hz: float = 2.0,
) -> float:
    """Return the strongest spectral bin at or above the high-pass cutoff."""
    if min_frequency_hz < 0.0:
        raise ValueError("min_frequency_hz must not be negative")
    spectrum = magnitude_spectrum(samples, sample_rate_hz)
    eligible = spectrum.frequencies_hz >= min_frequency_hz
    if not np.any(eligible):
        return 0.0
    eligible_indices = np.flatnonzero(eligible)
    peak_index = eligible_indices[np.argmax(spectrum.magnitudes[eligible])]
    return float(spectrum.frequencies_hz[peak_index])
