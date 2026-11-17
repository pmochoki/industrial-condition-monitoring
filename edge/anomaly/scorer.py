"""Explainable composite threshold and rolling-baseline scorer."""

from __future__ import annotations

from edge.anomaly.baseline import BaselineTracker
from edge.anomaly.config import ThresholdConfig
from edge.anomaly.thresholds import (
    Severity,
    ThresholdChecker,
    TriggeredRule,
    feature_values,
    normalized_deviations,
)
from edge.interfaces import AnomalyResult, FeatureVector


class CompositeScorer:
    """Compute a weighted, normalized feature-deviation score."""

    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config

    def score(self, values: dict[str, float]) -> float:
        deviations = normalized_deviations(values, self.config)
        weights = self.config.feature_weights
        total_weight = sum(weights.values())
        return min(
            1.0,
            max(
                0.0,
                sum(weights.get(name, 0.0) * deviations[name] for name in deviations)
                / total_weight,
            ),
        )


class StatusClassifier:
    """Select the worst severity across rules and composite thresholds."""

    def __init__(self, config: ThresholdConfig) -> None:
        self.config = config

    def classify(self, score: float, rules: list[TriggeredRule]) -> str:
        severity = max((rule.severity for rule in rules), default=Severity.NORMAL)
        if score >= self.config.composite_critical:
            severity = max(severity, Severity.CRITICAL)
        elif score >= self.config.composite_warning:
            severity = max(severity, Severity.WARNING)
        return severity.name


class ThresholdScorer:
    """ThresholdScorer implements the pluggable AnomalyScorer contract."""

    _FEATURE_KEYS = (
        "vibration_rms_g",
        "vibration_peak_g",
        "crest_factor",
        "dominant_frequency_hz",
        "temperature_c",
    )

    def __init__(self, config: ThresholdConfig) -> None:
        config.validate()
        self.config = config
        self.checker = ThresholdChecker(config)
        self.composite = CompositeScorer(config)
        self.classifier = StatusClassifier(config)
        self.baseline = BaselineTracker(
            self._FEATURE_KEYS,
            warmup_windows=config.baseline_warmup_windows,
            window_size=config.rolling_window_samples,
        )

    def score(self, features: FeatureVector) -> AnomalyResult:
        values = feature_values(features)
        rules = self.checker.evaluate(values)
        for key, z_score in self.baseline.z_scores(values).items():
            magnitude = abs(z_score)
            severity = (
                Severity.CRITICAL
                if magnitude > self.config.z_score_critical
                else (
                    Severity.WARNING
                    if magnitude > self.config.z_score_warning
                    else Severity.NORMAL
                )
            )
            if severity is not Severity.NORMAL:
                display_name = {
                    "vibration_rms_g": "vibration_rms",
                    "vibration_peak_g": "vibration_peak",
                    "dominant_frequency_hz": "dominant_frequency",
                    "temperature_c": "temperature",
                }.get(key, key)
                rules.append(
                    TriggeredRule(
                        f"z_score_{display_name}",
                        severity,
                        f"z_score_{display_name} > {severity.name.lower()} ({magnitude:.2f})",
                    )
                )

        score = self.composite.score(values)
        status = self.classifier.classify(score, rules)
        triggered = [rule.message for rule in rules]
        explanation = (
            "; ".join(triggered)
            if triggered
            else "All evaluated features are within configured limits."
        )
        result = AnomalyResult(status, score, triggered, explanation)  # type: ignore[arg-type]
        if status == "NORMAL":
            self.baseline.observe(values)
        return result
