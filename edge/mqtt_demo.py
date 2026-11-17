"""Run a simulator → edge pipeline → anomaly scorer → MQTT demo."""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import replace

from edge.anomaly.config import ThresholdConfig
from edge.anomaly.scorer import ThresholdScorer
from edge.mqtt.publisher import MqttPublisher, MqttSettings
from edge.pipeline import SignalProcessingPipeline
from simulator import CONDITIONS, Machine, MachineConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish simulated condition-monitoring telemetry to MQTT."
    )
    parser.add_argument(
        "--condition", choices=[item.value for item in CONDITIONS], default="normal"
    )
    parser.add_argument("--severity", type=float, default=0.0)
    parser.add_argument(
        "--windows", type=int, default=10, help="number of telemetry windows to publish"
    )
    parser.add_argument("--samples", type=int, default=1024, help="samples per window")
    parser.add_argument(
        "--interval-s",
        type=float,
        default=float(os.getenv("MQTT_TELEMETRY_INTERVAL_S", "1.0")),
        help="delay between publishes",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device-id", default="machine-001")
    parser.add_argument("--broker-host")
    parser.add_argument("--broker-port", type=int)
    parser.add_argument(
        "--thresholds", help="threshold YAML path (defaults to local file or example)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0.0 <= args.severity <= 1.0:
        raise SystemExit("--severity must be between 0.0 and 1.0")
    if args.windows <= 0 or args.samples <= 0 or args.interval_s < 0:
        raise SystemExit(
            "--windows and --samples must be positive; --interval-s cannot be negative"
        )

    settings = MqttSettings.load()
    settings = replace(
        settings,
        broker_host=args.broker_host or settings.broker_host,
        broker_port=args.broker_port or settings.broker_port,
    )
    machine = Machine(
        condition=args.condition,
        severity=args.severity,
        config=MachineConfig(device_id=args.device_id),
        seed=args.seed,
    )
    pipeline = SignalProcessingPipeline()
    scorer = ThresholdScorer(ThresholdConfig.load(args.thresholds))
    publisher = MqttPublisher(settings)
    publisher.connect(machine.device_id, machine.sample_rate_hz)
    try:
        for sequence in range(1, args.windows + 1):
            features = pipeline.process(machine.read_window(args.samples))
            anomaly = scorer.score(features)
            publisher.publish_telemetry(
                features, anomaly, sequence=sequence, source="simulator"
            )
            print(
                f"sequence={sequence} status={anomaly.status} "
                f"score={anomaly.anomaly_score:.3f} {anomaly.explanation}"
            )
            if sequence < args.windows and args.interval_s:
                time.sleep(args.interval_s)
    finally:
        publisher.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
