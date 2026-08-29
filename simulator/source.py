"""Source interfaces shared by simulation and future firmware adapters."""

from __future__ import annotations

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


# The simulator is already a concrete implementation of the source contract.
SimulatedMachine = Machine

__all__ = ["MachineDataSource", "RawSampleWindow", "SimulatedMachine", "MachineConfig"]
