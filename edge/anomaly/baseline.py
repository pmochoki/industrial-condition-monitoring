"""Rolling baseline and z-score tracking for machine features."""

from __future__ import annotations

import math
from collections import deque
from statistics import fmean, pstdev
from typing import Mapping


class BaselineTracker:
    """Track rolling normal-operation samples and expose z-scores."""

    def __init__(self, feature_keys: tuple[str, ...], warmup_windows: int, window_size: int) -> None:
        if warmup_windows <= 0 or window_size <= 0:
            raise ValueError("warmup_windows and window_size must be positive")
        self.warmup_windows = warmup_windows
        self._history = {key: deque[float](maxlen=window_size) for key in feature_keys}

    @property
    def sample_count(self) -> int:
        return min((len(samples) for samples in self._history.values()), default=0)

    @property
    def ready(self) -> bool:
        return self.sample_count >= self.warmup_windows

    def z_scores(self, values: Mapping[str, float]) -> dict[str, float]:
        """Compute z-scores from history before the current sample is observed."""
        if not self.ready:
            return {}
        scores: dict[str, float] = {}
        for key, samples in self._history.items():
            if key not in values or not samples:
                continue
            mean = fmean(samples)
            deviation = pstdev(samples)
            delta = values[key] - mean
            if deviation == 0.0:
                scores[key] = 0.0 if delta == 0.0 else math.copysign(math.inf, delta)
            else:
                scores[key] = delta / deviation
        return scores

    def observe(self, values: Mapping[str, float]) -> None:
        """Append one accepted (normal-status) sample to the rolling baseline."""
        for key, samples in self._history.items():
            value = values.get(key)
            if value is not None and math.isfinite(value):
                samples.append(float(value))
