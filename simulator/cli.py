"""Command-line interface for generating synthetic machine data."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import TextIO

from simulator.conditions import CONDITIONS
from simulator.models.machine import Machine, MachineConfig, RawSampleWindow


CSV_FIELDS = (
    "timestamp",
    "device_id",
    "condition",
    "severity",
    "sample_rate_hz",
    "sample_index",
    "ax_g",
    "ay_g",
    "az_g",
    "temperature_c",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate physics-informed rotating-machine data.")
    parser.add_argument(
        "--condition",
        choices=[condition.value for condition in CONDITIONS],
        default="normal",
        help="machine condition to simulate (default: normal)",
    )
    parser.add_argument("--severity", type=float, default=0.0, help="fault severity from 0.0 to 1.0")
    parser.add_argument("--samples", type=int, default=1024, help="samples per window (default: 1024)")
    parser.add_argument("--windows", type=int, default=1, help="number of contiguous windows (default: 1)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    parser.add_argument("--device-id", default="machine-001")
    parser.add_argument("--shaft-speed-rpm", type=float, default=1200.0)
    parser.add_argument("--sample-rate-hz", type=int, default=2048)
    parser.add_argument("--noise-floor-g", type=float, default=0.002)
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--output", default="-", help="output path, or - for stdout")
    return parser


def _window_rows(window: RawSampleWindow, sample_offset: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (ax, ay, az) in enumerate(zip(window.ax_g, window.ay_g, window.az_g, strict=True)):
        rows.append(
            {
                "timestamp": window.timestamp.isoformat(),
                "device_id": window.device_id,
                "condition": window.condition.value,
                "severity": window.severity,
                "sample_rate_hz": window.sample_rate_hz,
                "sample_index": sample_offset + index,
                "ax_g": ax,
                "ay_g": ay,
                "az_g": az,
                "temperature_c": window.temperature_c,
            }
        )
    return rows


def _write_csv(windows: list[RawSampleWindow], stream: TextIO) -> None:
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
    writer.writeheader()
    offset = 0
    for window in windows:
        writer.writerows(_window_rows(window, offset))
        offset += window.sample_count


def _write_json(windows: list[RawSampleWindow], stream: TextIO) -> None:
    rows: list[dict[str, object]] = []
    offset = 0
    for window in windows:
        rows.extend(_window_rows(window, offset))
        offset += window.sample_count
    json.dump(
        {
            "device_id": windows[0].device_id,
            "condition": windows[0].condition.value,
            "severity": windows[0].severity,
            "sample_rate_hz": windows[0].sample_rate_hz,
            "samples": rows,
        },
        stream,
        indent=2,
    )
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0.0 <= args.severity <= 1.0:
        raise SystemExit("--severity must be between 0.0 and 1.0")
    if args.samples <= 0 or args.windows <= 0:
        raise SystemExit("--samples and --windows must be positive")

    machine = Machine(
        condition=args.condition,
        severity=args.severity,
        config=MachineConfig(
            device_id=args.device_id,
            shaft_speed_rpm=args.shaft_speed_rpm,
            sample_rate_hz=args.sample_rate_hz,
            noise_floor_g=args.noise_floor_g,
        ),
        seed=args.seed,
    )
    windows = [machine.read_window(args.samples) for _ in range(args.windows)]

    if args.output == "-":
        stream = sys.stdout
        close_stream = False
    else:
        stream = open(args.output, "w", newline="", encoding="utf-8")
        close_stream = True
    try:
        if args.format == "csv":
            _write_csv(windows, stream)
        else:
            _write_json(windows, stream)
    finally:
        if close_stream:
            stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
