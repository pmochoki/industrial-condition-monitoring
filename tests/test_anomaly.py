from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from edge.anomaly.baseline import BaselineTracker
from edge.anomaly.config import ThresholdConfig
from edge.anomaly.scorer import CompositeScorer, ThresholdScorer
from edge.interfaces import FeatureVector
from edge.pipeline import SignalProcessingPipeline
from simulator import Machine, MachineCondition, MachineConfig


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_features(**changes: float) -> FeatureVector:
    values = {
        "timestamp": START,
        "device_id": "machine-001",
        "temperature_c": 45.0,
        "vibration_x": 0.0,
        "vibration_y": 0.0,
        "vibration_z": 0.0,
        "vibration_rms": 0.05,
        "vibration_peak": 0.15,
        "vibration_peak_to_peak": 0.30,
        "vibration_std": 0.05,
        "crest_factor": 3.0,
        "dominant_frequency_hz": 20.0,
    }
    values.update(changes)
    return FeatureVector(**values)


@pytest.fixture
def config() -> ThresholdConfig:
    return ThresholdConfig.load()


def test_normal_features_are_normal_and_explainable(config: ThresholdConfig) -> None:
    result = ThresholdScorer(config).score(make_features())

    assert result.status == "NORMAL"
    assert 0.0 <= result.anomaly_score <= 1.0
    assert result.triggered_rules == []
    assert "within configured limits" in result.explanation


def test_absolute_warning_includes_triggered_rule(config: ThresholdConfig) -> None:
    result = ThresholdScorer(config).score(make_features(vibration_rms=0.13))

    assert result.status == "WARNING"
    assert result.triggered_rules[0].startswith("vibration_rms_g > warning")
    assert "0.130" in result.explanation


def test_absolute_critical_takes_precedence(config: ThresholdConfig) -> None:
    result = ThresholdScorer(config).score(make_features(vibration_rms=0.30))

    assert result.status == "CRITICAL"
    assert any("vibration_rms_g > critical" in rule for rule in result.triggered_rules)


def test_dominant_frequency_uses_deviation_from_machine_baseline(config: ThresholdConfig) -> None:
    result = ThresholdScorer(config).score(make_features(dominant_frequency_hz=27.0))

    assert result.status == "WARNING"
    assert any("dominant_frequency_hz deviation > warning" in rule for rule in result.triggered_rules)


def test_baseline_warms_up_and_detects_outlier(config: ThresholdConfig) -> None:
    tracker = BaselineTracker(("temperature_c",), warmup_windows=3, window_size=10)
    for value in (45.0, 45.0, 45.0):
        tracker.observe({"temperature_c": value})
    assert tracker.ready
    assert tracker.z_scores({"temperature_c": 50.0})["temperature_c"] == float("inf")


def test_scorer_emits_z_score_rule_after_warmup(config: ThresholdConfig) -> None:
    tuned = replace(config, baseline_warmup_windows=3)
    scorer = ThresholdScorer(tuned)
    for _ in range(3):
        assert scorer.score(make_features()).status == "NORMAL"

    result = scorer.score(make_features(temperature_c=50.0))
    assert result.status == "CRITICAL"
    assert any(rule.startswith("z_score_temperature > critical") for rule in result.triggered_rules)


def test_composite_score_is_bounded(config: ThresholdConfig) -> None:
    scorer = CompositeScorer(config)
    normal = {"vibration_rms_g": 0.05, "vibration_peak_g": 0.15, "crest_factor": 3.0, "dominant_frequency_hz": 40.0, "temperature_c": 45.0}
    severe = {**normal, "vibration_rms_g": 1.0, "vibration_peak_g": 2.0, "crest_factor": 10.0, "temperature_c": 100.0}

    assert scorer.score(normal) == pytest.approx(0.0)
    assert scorer.score(severe) == pytest.approx(1.0)


def test_simulated_excessive_vibration_triggers_warning_or_critical(config: ThresholdConfig) -> None:
    machine = Machine(
        MachineCondition.EXCESSIVE_VIBRATION,
        severity=1.0,
        config=MachineConfig(start_time=START),
        seed=11,
    )
    features = SignalProcessingPipeline().process(machine.read_window(1024))
    result = ThresholdScorer(config).score(features)

    assert result.status in {"WARNING", "CRITICAL"}
    assert result.triggered_rules
