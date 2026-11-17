"""Absolute threshold checks and normalized feature deviations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping

from edge.anomaly.config import ThresholdConfig
from edge.interfaces import FeatureVector


class Severity(IntEnum):
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


@dataclass(frozen=True)
class TriggeredRule:
    name: str
    severity: Severity
    message: str


def feature_values(features: FeatureVector) -> dict[str, float]:
    return {
        "vibration_rms_g": features.vibration_rms,
        "vibration_peak_g": features.vibration_peak,
        "crest_factor": features.crest_factor,
        "dominant_frequency_hz": features.dominant_frequency_hz,
        "temperature_c": features.temperature_c,
    }


class ThresholdChecker:
    """Evaluate the configured absolute limits for one feature vector."""

    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config

    def evaluate(self, values: Mapping[str, float]) -> list[TriggeredRule]:
        rules: list[TriggeredRule] = []
        for name in ("vibration_rms_g", "vibration_peak_g", "crest_factor", "temperature_c"):
            value = values[name]
            limits = self.config.thresholds[name]
            severity = Severity.CRITICAL if value > limits["critical"] else (
                Severity.WARNING if value > limits["warning"] else Severity.NORMAL
            )
            if severity is not Severity.NORMAL:
                level = severity.name.lower()
                rules.append(TriggeredRule(name, severity, f"{name} > {level} ({value:.3f} > {limits[level]:.3f})"))

        name = "dominant_frequency_hz"
        value = values[name]
        deviation = abs(value - self.config.baseline[name])
        limits = self.config.thresholds[name]
        severity = Severity.CRITICAL if deviation > limits["critical_deviation"] else (
            Severity.WARNING if deviation > limits["warning_deviation"] else Severity.NORMAL
        )
        if severity is not Severity.NORMAL:
            level = severity.name.lower()
            limit = limits[f"{level}_deviation"]
            rules.append(TriggeredRule(name, severity, f"{name} deviation > {level} ({deviation:.3f} > {limit:.3f} Hz)"))
        return rules


def normalized_deviations(values: Mapping[str, float], config: ThresholdConfig) -> dict[str, float]:
    """Map configured feature deviations to 0–1 for the composite score."""
    names = {
        "vibration_rms": "vibration_rms_g",
        "vibration_peak": "vibration_peak_g",
        "crest_factor": "crest_factor",
        "dominant_frequency": "dominant_frequency_hz",
        "temperature": "temperature_c",
    }
    result: dict[str, float] = {}
    for weight_name, name in names.items():
        value = values[name]
        baseline = config.baseline[name]
        limits = config.thresholds[name]
        if name == "dominant_frequency_hz":
            ratio = abs(value - baseline) / limits["warning_deviation"]
        else:
            ratio = (value - baseline) / (limits["warning"] - baseline)
        result[weight_name] = min(1.0, max(0.0, ratio))
    return result
