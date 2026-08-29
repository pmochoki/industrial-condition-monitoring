from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import pytest

from simulator import Machine, MachineCondition, MachineConfig
from simulator.cli import main


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
CONFIG = MachineConfig(start_time=START, sample_rate_hz=2048, shaft_speed_rpm=1200.0)


def _amplitude_at(values: list[float], frequency_hz: float, sample_rate_hz: int) -> float:
    """Estimate a sinusoid amplitude using in-phase/quadrature projections."""
    count = len(values)
    cosine = sum(value * math.cos(2.0 * math.pi * frequency_hz * i / sample_rate_hz) for i, value in enumerate(values))
    sine = sum(value * math.sin(2.0 * math.pi * frequency_hz * i / sample_rate_hz) for i, value in enumerate(values))
    return 2.0 * math.hypot(cosine, sine) / count


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def test_same_seed_produces_same_window() -> None:
    first = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(128)
    second = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(128)

    assert first.timestamp == second.timestamp
    assert first.ax_g == second.ax_g
    assert first.ay_g == second.ay_g
    assert first.temperature_c == second.temperature_c


def test_imbalance_increases_one_x_shaft_frequency() -> None:
    normal = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(2048)
    imbalance = Machine(MachineCondition.IMBALANCE, severity=1.0, config=CONFIG, seed=7).read_window(2048)

    normal_1x = _amplitude_at(normal.ax_g, 20.0, CONFIG.sample_rate_hz)
    imbalance_1x = _amplitude_at(imbalance.ax_g, 20.0, CONFIG.sample_rate_hz)
    assert imbalance_1x > normal_1x + 0.06


def test_misalignment_increases_two_x_shaft_frequency() -> None:
    normal = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(2048)
    misalignment = Machine(MachineCondition.MISALIGNMENT, severity=1.0, config=CONFIG, seed=7).read_window(2048)

    normal_2x = _amplitude_at(normal.ax_g, 40.0, CONFIG.sample_rate_hz)
    misalignment_2x = _amplitude_at(misalignment.ax_g, 40.0, CONFIG.sample_rate_hz)
    assert misalignment_2x > normal_2x + 0.04


def test_bearing_degradation_creates_impulses() -> None:
    normal = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(2048)
    bearing = Machine(MachineCondition.BEARING_DEGRADATION, severity=1.0, config=CONFIG, seed=7).read_window(2048)

    assert max(abs(value) for value in bearing.ax_g) > max(abs(value) for value in normal.ax_g) + 0.10


def test_temperature_fault_drifts_across_windows() -> None:
    machine = Machine(MachineCondition.TEMPERATURE_INCREASE, severity=1.0, config=CONFIG, seed=7)
    first = machine.read_window(1024).temperature_c
    last = machine.read_window(1024).temperature_c

    assert last > first + 4.0
    assert machine.read_temperature() == last


def test_sensor_noise_increases_rms() -> None:
    normal = Machine(MachineCondition.NORMAL, config=CONFIG, seed=7).read_window(2048)
    noisy = Machine(MachineCondition.SENSOR_NOISE, severity=1.0, config=CONFIG, seed=7).read_window(2048)

    assert _rms(noisy.ax_g) > _rms(normal.ax_g) * 1.8


def test_invalid_severity_is_rejected() -> None:
    with pytest.raises(ValueError, match="severity"):
        Machine(MachineCondition.IMBALANCE, severity=1.1, config=CONFIG)


def test_cli_emits_json_samples(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--condition", "imbalance", "--severity", "0.5", "--samples", "3", "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["condition"] == "imbalance"
    assert payload["severity"] == 0.5
    assert len(payload["samples"]) == 3
    assert payload["samples"][0]["device_id"] == "machine-001"
