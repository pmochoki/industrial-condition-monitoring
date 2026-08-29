from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from edge.features.frequency_domain import dominant_frequency_hz
from edge.features.time_domain import as_resultant, compute_time_domain_features
from edge.filtering.butterworth import bandpass_filter
from edge.filtering.detrend import remove_dc_offset
from edge.pipeline import SignalProcessingPipeline
from simulator import Machine, MachineConfig


SAMPLE_RATE = 2048


def _amplitude_at(values: np.ndarray, frequency_hz: float) -> float:
    count = values.size
    time = np.arange(count) / SAMPLE_RATE
    cosine = np.sum(values * np.cos(2.0 * np.pi * frequency_hz * time))
    sine = np.sum(values * np.sin(2.0 * np.pi * frequency_hz * time))
    return float(2.0 * np.hypot(cosine, sine) / count)


def test_resultant_combines_three_axes() -> None:
    resultant = as_resultant([3.0, 0.0], [4.0, 0.0], [0.0, 12.0])

    np.testing.assert_allclose(resultant, [5.0, 12.0])


def test_rms_of_one_g_sine_is_sqrt_half() -> None:
    time = np.arange(SAMPLE_RATE) / SAMPLE_RATE
    features = compute_time_domain_features(np.sin(2.0 * np.pi * 50.0 * time))

    assert features.rms == pytest.approx(np.sqrt(0.5), abs=1e-6)
    assert features.peak == pytest.approx(1.0, abs=1e-6)
    assert features.crest_factor == pytest.approx(np.sqrt(2.0), abs=1e-6)


def test_dominant_frequency_uses_two_hz_bins() -> None:
    time = np.arange(1024) / SAMPLE_RATE
    samples = np.sin(2.0 * np.pi * 20.0 * time)

    assert dominant_frequency_hz(samples, SAMPLE_RATE) == pytest.approx(20.0, abs=2.0)


def test_bandpass_rejects_half_hz_and_passes_fifty_hz() -> None:
    time = np.arange(4096) / SAMPLE_RATE
    low = 0.8 * np.sin(2.0 * np.pi * 0.5 * time)
    passed = 1.0 * np.sin(2.0 * np.pi * 50.0 * time)
    filtered = bandpass_filter(low + passed, SAMPLE_RATE)

    assert _amplitude_at(filtered, 0.5) < 0.1
    assert _amplitude_at(filtered, 50.0) > 0.7


def test_dc_offset_removal_centres_signal() -> None:
    time = np.arange(1024) / SAMPLE_RATE
    centred = remove_dc_offset(4.5 + np.sin(2.0 * np.pi * 20.0 * time))

    assert float(np.mean(centred)) == pytest.approx(0.0, abs=1e-12)


def test_pipeline_processes_simulator_window() -> None:
    machine = Machine(
        config=MachineConfig(
            sample_rate_hz=SAMPLE_RATE,
            shaft_speed_rpm=1200.0,
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
        seed=42,
    )
    window = machine.read_window(1024)
    features = SignalProcessingPipeline().process(window)

    assert features.device_id == "machine-001"
    assert features.timestamp == window.timestamp
    assert features.temperature_c == pytest.approx(window.temperature_c)
    assert features.vibration_rms > 0.0
    assert features.vibration_peak >= features.vibration_rms
    assert features.dominant_frequency_hz == pytest.approx(20.0, abs=2.0)
