"""Pre-processing helpers for raw acceleration signals."""

from __future__ import annotations

import numpy as np


def remove_dc_offset(samples: np.ndarray | list[float]) -> np.ndarray:
    """Return samples centred around zero without changing their shape."""
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("samples must be a non-empty one-dimensional sequence")
    return values - np.mean(values)
