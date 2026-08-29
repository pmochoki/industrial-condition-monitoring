"""Time-domain features for resultant vibration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TimeDomainFeatures:
    mean: float
    rms: float
    peak: float
    peak_to_peak: float
    std_dev: float
    crest_factor: float


def as_resultant(
    ax_g: np.ndarray | list[float],
    ay_g: np.ndarray | list[float],
    az_g: np.ndarray | list[float],
) -> np.ndarray:
    """Combine three acceleration axes into resultant acceleration."""
    axes = [np.asarray(axis, dtype=float) for axis in (ax_g, ay_g, az_g)]
    if any(axis.ndim != 1 or axis.size == 0 for axis in axes):
        raise ValueError("all axes must be non-empty one-dimensional sequences")
    if len({axis.size for axis in axes}) != 1:
        raise ValueError("all axes must have the same number of samples")
    return np.sqrt(axes[0] ** 2 + axes[1] ** 2 + axes[2] ** 2)


def compute_time_domain_features(samples: np.ndarray | list[float]) -> TimeDomainFeatures:
    """Compute the Phase 3 feature set on one signal, in g."""
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("samples must be a non-empty one-dimensional sequence")
    mean = float(np.mean(values))
    rms = float(np.sqrt(np.mean(values**2)))
    peak = float(np.max(np.abs(values)))
    peak_to_peak = float(np.max(values) - np.min(values))
    std_dev = float(np.std(values))
    crest_factor = peak / rms if rms > 0.0 else 0.0
    return TimeDomainFeatures(mean, rms, peak, peak_to_peak, std_dev, crest_factor)
