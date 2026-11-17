from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from edge.interfaces import AnomalyResult, FeatureVector
from edge.mqtt.publisher import MqttPublisher, MqttSettings


class FakeInfo:
    rc = 0

    def wait_for_publish(self, timeout: float) -> None:
        return None

    def is_published(self) -> bool:
        return True


class FakeClient:
    def __init__(self) -> None:
        self.will = None
        self.published = []
        self.connected_to = None
        self.started = False
        self.stopped = False
        self.disconnected = False

    def will_set(self, topic: str, payload: str, qos: int, retain: bool) -> None:
        self.will = (topic, json.loads(payload), qos, retain)

    def username_pw_set(self, username: str, password: str | None) -> None:
        raise AssertionError("credentials are not expected in this test")

    def tls_set(self) -> None:
        raise AssertionError("TLS is not expected in this test")

    def connect(self, host: str, port: int, keepalive: int) -> int:
        self.connected_to = (host, port, keepalive)
        return 0

    def loop_start(self) -> None:
        self.started = True

    def loop_stop(self) -> None:
        self.stopped = True

    def disconnect(self) -> None:
        self.disconnected = True

    def publish(self, topic: str, payload: str, qos: int, retain: bool) -> FakeInfo:
        self.published.append((topic, json.loads(payload), qos, retain))
        return FakeInfo()


def features(status_time: datetime | None = None) -> FeatureVector:
    return FeatureVector(
        timestamp=status_time or datetime(2026, 1, 1, tzinfo=UTC),
        device_id="machine-001",
        temperature_c=45.0,
        vibration_x=0.01,
        vibration_y=0.02,
        vibration_z=0.03,
        vibration_rms=0.05,
        vibration_peak=0.15,
        vibration_peak_to_peak=0.30,
        vibration_std=0.05,
        crest_factor=3.0,
        dominant_frequency_hz=20.0,
    )


def anomaly(status: str, score: float = 0.1) -> AnomalyResult:
    rules = [] if status == "NORMAL" else ["vibration_rms_g > warning"]
    return AnomalyResult(
        status,
        score,
        rules,
        "All features normal." if not rules else "Vibration RMS exceeded warning.",
    )  # type: ignore[arg-type]


def setup_publisher() -> tuple[MqttPublisher, FakeClient]:
    client = FakeClient()
    publisher = MqttPublisher(MqttSettings(broker_host="localhost"), client=client)
    publisher.connect("machine-001", 2048)
    return publisher, client


def test_connect_sets_offline_last_will_and_retained_online_status() -> None:
    publisher, client = setup_publisher()

    assert client.will is not None
    assert client.will[0] == "machines/machine-001/status"
    assert client.will[1]["online"] is False
    assert client.will[2:] == (1, True)
    topic, payload, qos, retained = client.published[0]
    assert topic == "machines/machine-001/status"
    assert payload["online"] is True
    assert payload["sample_rate_hz"] == 2048
    assert qos == 1 and retained is True
    publisher.close()


def test_telemetry_matches_documented_json_schema() -> None:
    publisher, client = setup_publisher()
    publisher.publish_telemetry(features(), anomaly("NORMAL"), sequence=7)

    topic, payload, qos, retained = client.published[-1]
    assert topic == "machines/machine-001/telemetry"
    assert payload["sequence"] == 7
    assert payload["source"] == "simulator"
    assert payload["machine_status"] == "NORMAL"
    assert payload["vibration"]["rms"] == 0.05
    assert qos == 1 and retained is False
    publisher.close()


def test_alerts_are_published_only_on_status_transitions() -> None:
    publisher, client = setup_publisher()
    publisher.publish_telemetry(features(), anomaly("NORMAL"), sequence=1)
    publisher.publish_telemetry(features(), anomaly("WARNING", 0.5), sequence=2)
    publisher.publish_telemetry(features(), anomaly("WARNING", 0.6), sequence=3)
    publisher.publish_telemetry(features(), anomaly("NORMAL"), sequence=4)

    alerts = [
        item for item in client.published if item[0] == "machines/machine-001/alerts"
    ]
    assert len(alerts) == 2
    assert alerts[0][1]["previous_status"] == "NORMAL"
    assert alerts[0][1]["current_status"] == "WARNING"
    assert alerts[1][1]["previous_status"] == "WARNING"
    assert alerts[1][1]["current_status"] == "NORMAL"
    publisher.close()


def test_graceful_close_publishes_offline_status() -> None:
    publisher, client = setup_publisher()
    publisher.close()

    topic, payload, qos, retained = client.published[-1]
    assert topic == "machines/machine-001/status"
    assert payload["online"] is False
    assert qos == 1 and retained is True
    assert client.stopped and client.disconnected


def test_rejects_invalid_device_id_and_score() -> None:
    client = FakeClient()
    publisher = MqttPublisher(MqttSettings(broker_host="localhost"), client=client)
    with pytest.raises(ValueError, match="topic segment"):
        publisher.connect("machine/one", 2048)

    publisher, _ = setup_publisher()
    with pytest.raises(ValueError, match="anomaly_score"):
        publisher.publish_telemetry(features(), anomaly("WARNING", 1.5), sequence=1)
    publisher.close()
