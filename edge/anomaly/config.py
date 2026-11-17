"""Load and validate per-machine fault-detection configuration."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


@dataclass(frozen=True)
class ThresholdConfig:
    device_id: str
    baseline: Mapping[str, float]
    thresholds: Mapping[str, Mapping[str, float]]
    z_score_warning: float
    z_score_critical: float
    rolling_window_samples: int
    composite_warning: float
    composite_critical: float
    feature_weights: Mapping[str, float]
    baseline_warmup_windows: int = 60

    @classmethod
    def load(
        cls,
        path: str | Path | None = None,
        default_config_path: str | Path = "config/default.yaml",
    ) -> "ThresholdConfig":
        """Load thresholds and anomaly weights from YAML files.

        If the local thresholds.yaml is absent, use the committed example so
        that a cloned repository can run the demo without manual setup.
        """
        threshold_path = Path(path) if path else Path(os.getenv("THRESHOLDS_PATH", "config/thresholds.yaml"))
        if not threshold_path.exists():
            threshold_path = Path("config/thresholds.example.yaml")
        raw = yaml.safe_load(threshold_path.read_text(encoding="utf-8"))
        defaults = yaml.safe_load(Path(default_config_path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(defaults, dict):
            raise ValueError("threshold and default configuration files must contain YAML mappings")

        baseline = _number_mapping(raw.get("baseline"), "baseline")
        threshold_sections = raw.get("thresholds")
        if not isinstance(threshold_sections, dict):
            raise ValueError("thresholds must be a YAML mapping")
        thresholds = {
            str(name): _number_mapping(values, f"thresholds.{name}")
            for name, values in threshold_sections.items()
        }
        statistical = raw.get("statistical", {})
        composite = raw.get("composite_score", {})
        anomaly = defaults.get("anomaly_detection", {})
        if not all(isinstance(section, dict) for section in (statistical, composite, anomaly)):
            raise ValueError("statistical, composite_score, and anomaly_detection must be mappings")
        weights = _number_mapping(anomaly.get("feature_weights"), "anomaly_detection.feature_weights")
        config = cls(
            device_id=str(raw.get("device_id", "machine-001")),
            baseline=baseline,
            thresholds=thresholds,
            z_score_warning=_finite_number(statistical.get("z_score_warning"), "z_score_warning"),
            z_score_critical=_finite_number(statistical.get("z_score_critical"), "z_score_critical"),
            rolling_window_samples=_positive_int(statistical.get("rolling_window_samples"), "rolling_window_samples"),
            composite_warning=_finite_number(composite.get("warning"), "composite warning"),
            composite_critical=_finite_number(composite.get("critical"), "composite critical"),
            feature_weights=weights,
            baseline_warmup_windows=_positive_int(anomaly.get("baseline_warmup_windows", 60), "baseline_warmup_windows"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        required_baselines = {"vibration_rms_g", "vibration_peak_g", "crest_factor", "dominant_frequency_hz", "temperature_c"}
        required_thresholds = set(required_baselines)
        if required_baselines - self.baseline.keys():
            raise ValueError(f"missing baseline values: {sorted(required_baselines - self.baseline.keys())}")
        if required_thresholds - self.thresholds.keys():
            raise ValueError(f"missing feature thresholds: {sorted(required_thresholds - self.thresholds.keys())}")
        for name in ("vibration_rms_g", "vibration_peak_g", "crest_factor", "temperature_c"):
            limits = self.thresholds[name]
            if not {"warning", "critical"}.issubset(limits):
                raise ValueError(f"{name} requires warning and critical limits")
            if not self.baseline[name] < limits["warning"] < limits["critical"]:
                raise ValueError(f"{name} thresholds must be above baseline and increasing")
        frequency = self.thresholds["dominant_frequency_hz"]
        if not {"warning_deviation", "critical_deviation"}.issubset(frequency):
            raise ValueError("dominant_frequency_hz requires deviation thresholds")
        if not 0 < frequency["warning_deviation"] < frequency["critical_deviation"]:
            raise ValueError("frequency deviation thresholds must be positive and increasing")
        if not 0 < self.z_score_warning < self.z_score_critical:
            raise ValueError("z-score thresholds must be positive and increasing")
        if not 0 <= self.composite_warning < self.composite_critical <= 1:
            raise ValueError("composite thresholds must satisfy 0 <= warning < critical <= 1")
        if not self.feature_weights or any(weight < 0 for weight in self.feature_weights.values()):
            raise ValueError("feature weights must be non-negative and contain at least one value")
        if sum(self.feature_weights.values()) <= 0:
            raise ValueError("at least one feature weight must be positive")


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _number_mapping(value: object, name: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a YAML mapping")
    return {str(key): _finite_number(item, f"{name}.{key}") for key, item in value.items()}


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value
