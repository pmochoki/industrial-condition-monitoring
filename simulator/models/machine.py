"""Physics-informed rotating-machine signal generator."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from simulator.conditions import MachineCondition
from simulator.models.faults import FaultProfile, profile_for
from simulator.models.noise import NoiseModel


@dataclass(frozen=True)
class MachineConfig:
    """Configuration shared by simulator and future hardware sources."""

    device_id: str = "machine-001"
    shaft_speed_rpm: float = 1200.0
    sample_rate_hz: int = 2048
    noise_floor_g: float = 0.002
    base_temperature_c: float = 35.0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.device_id.strip():
            raise ValueError("device_id must not be empty")
        if self.shaft_speed_rpm <= 0:
            raise ValueError("shaft_speed_rpm must be positive")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.noise_floor_g < 0:
            raise ValueError("noise_floor_g must not be negative")


@dataclass
class RawSampleWindow:
    """A window of raw samples before edge signal processing."""

    timestamp: datetime
    device_id: str
    sample_rate_hz: int
    ax_g: list[float]
    ay_g: list[float]
    az_g: list[float]
    temperature_c: float
    condition: MachineCondition
    severity: float

    @property
    def sample_count(self) -> int:
        return len(self.ax_g)

    @property
    def duration_s(self) -> float:
        return self.sample_count / self.sample_rate_hz


class Machine:
    """Generate deterministic synthetic data for a rotating machine scenario."""

    def __init__(
        self,
        condition: MachineCondition | str = MachineCondition.NORMAL,
        severity: float = 0.0,
        config: MachineConfig | None = None,
        seed: int | None = None,
    ) -> None:
        self.condition = (
            MachineCondition.parse(condition) if isinstance(condition, str) else condition
        )
        if not 0.0 <= severity <= 1.0:
            raise ValueError("severity must be between 0.0 and 1.0")
        self.severity = severity
        self.config = config or MachineConfig()
        self.profile: FaultProfile = profile_for(self.condition, severity)
        self.noise = NoiseModel(vibration_std_g=self.config.noise_floor_g)
        self._rng = random.Random(seed)
        self._sample_index = 0
        self._last_temperature_c = self.config.base_temperature_c

    @property
    def device_id(self) -> str:
        return self.config.device_id

    @property
    def sample_rate_hz(self) -> int:
        return self.config.sample_rate_hz

    @property
    def shaft_frequency_hz(self) -> float:
        return self.config.shaft_speed_rpm / 60.0

    def read_temperature(self) -> float:
        """Return the most recently generated temperature reading."""
        return self._last_temperature_c

    def read_window(self, window_size: int = 1024) -> RawSampleWindow:
        """Generate the next contiguous raw-sample window."""
        if window_size <= 0:
            raise ValueError("window_size must be positive")

        start_index = self._sample_index
        start_seconds = start_index / self.sample_rate_hz
        ax: list[float] = []
        ay: list[float] = []
        az: list[float] = []
        temperature_samples: list[float] = []

        for offset in range(window_size):
            seconds = (start_index + offset) / self.sample_rate_hz
            ax_value, ay_value, az_value = self._vibration_sample(seconds)
            temperature = (
                self.config.base_temperature_c
                + self.profile.temperature_rise_c_per_second * seconds
                + self.noise.temperature(self._rng)
            )
            ax.append(ax_value)
            ay.append(ay_value)
            az.append(az_value)
            temperature_samples.append(temperature)

        self._sample_index += window_size
        self._last_temperature_c = sum(temperature_samples) / len(temperature_samples)
        timestamp = self._timestamp_at(start_seconds)
        return RawSampleWindow(
            timestamp=timestamp,
            device_id=self.device_id,
            sample_rate_hz=self.sample_rate_hz,
            ax_g=ax,
            ay_g=ay,
            az_g=az,
            temperature_c=self._last_temperature_c,
            condition=self.condition,
            severity=self.severity,
        )

    def _timestamp_at(self, seconds: float) -> datetime:
        start = self.config.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        return start + timedelta(seconds=seconds)

    def _vibration_sample(self, seconds: float) -> tuple[float, float, float]:
        omega = 2.0 * math.pi * self.shaft_frequency_hz
        base_x = 0.025 * math.sin(omega * seconds)
        base_y = 0.018 * math.sin(omega * seconds + math.pi / 2.0)
        base_z = 0.012 * math.sin(omega * seconds + math.pi / 4.0)

        imbalance_x = self.profile.vibration_1x_g * math.sin(omega * seconds)
        imbalance_y = self.profile.vibration_1x_g * math.sin(omega * seconds + math.pi / 2.0)
        misalignment_x = (
            self.profile.vibration_2x_g * math.sin(2.0 * omega * seconds)
            + self.profile.vibration_3x_g * math.sin(3.0 * omega * seconds)
        )
        misalignment_y = (
            self.profile.vibration_2x_g * math.sin(2.0 * omega * seconds + math.pi / 2.0)
            + self.profile.vibration_3x_g * math.sin(3.0 * omega * seconds + math.pi / 4.0)
        )
        bearing = self.profile.bearing_harmonic_g * math.sin(8.0 * omega * seconds)
        impulse = self._impulse(seconds)
        noise_multiplier = self.profile.noise_multiplier

        return (
            base_x + imbalance_x + misalignment_x + bearing + impulse
            + self.noise.vibration(self._rng, noise_multiplier),
            base_y + imbalance_y + misalignment_y + bearing + impulse
            + self.noise.vibration(self._rng, noise_multiplier),
            base_z + 0.5 * misalignment_x + 0.5 * bearing + impulse
            + self.noise.vibration(self._rng, noise_multiplier),
        )

    def _impulse(self, seconds: float) -> float:
        interval = self.profile.impulse_interval_s
        if interval <= 0.0:
            return 0.0
        phase = seconds % interval
        pulse_duration = min(0.025, interval / 4.0)
        if phase >= pulse_duration:
            return 0.0
        envelope = 1.0 - (phase / pulse_duration)
        return self.profile.impulse_amplitude_g * envelope
