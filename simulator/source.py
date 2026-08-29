"""Source interfaces shared by simulation and future firmware adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from simulator.models.machine import Machine, MachineConfig, RawSampleWindow


class MachineDataSource(Protocol):
    """Contract that the simulator and hardware source must both implement."""

    def read_window(self, window_size: int = 1024) -> RawSampleWindow: ...

    def read_temperature(self) -> float: ...

    @property
    def device_id(self) -> str: ...

    @property
    def sample_rate_hz(self) -> int: ...


class SimulatedMachine(Machine):
    """Named adapter for callers that depend on the source abstraction."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]


__all__ = ["MachineDataSource", "RawSampleWindow", "SimulatedMachine", "MachineConfig", "datetime"]
