"""MQTT publisher for telemetry, retained status, and status-transition alerts."""

from __future__ import annotations

import json
import math
import os
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt
import yaml

from edge.interfaces import AnomalyResult, FeatureVector


@dataclass(frozen=True)
class MqttSettings:
    broker_host: str
    broker_port: int = 1883
    client_id: str = "condition-monitor-001"
    topic_prefix: str = "machines"
    qos: int = 1
    retain_status: bool = True
    use_tls: bool = False
    username: str | None = None
    password: str | None = None
    keepalive_s: int = 60

    @classmethod
    def load(cls, path: str | Path = "config/default.yaml") -> MqttSettings:
        """Load broker defaults from YAML and apply MQTT_* environment overrides."""
        config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        section = config.get("mqtt", {}) if isinstance(config, dict) else {}
        if not isinstance(section, dict):
            raise ValueError("mqtt configuration must be a YAML mapping")
        username = os.getenv("MQTT_USERNAME") or None
        password = os.getenv("MQTT_PASSWORD") or None
        if bool(username) != bool(password):
            raise ValueError("MQTT_USERNAME and MQTT_PASSWORD must be set together")
        settings = cls(
            broker_host=os.getenv(
                "MQTT_BROKER_HOST", str(section.get("broker_host", "localhost"))
            ),
            broker_port=int(
                os.getenv("MQTT_BROKER_PORT", section.get("broker_port", 1883))
            ),
            client_id=os.getenv("MQTT_CLIENT_ID", "condition-monitor-001"),
            topic_prefix=os.getenv(
                "MQTT_TOPIC_PREFIX", str(section.get("topic_prefix", "machines"))
            ),
            qos=int(section.get("qos", 1)),
            retain_status=bool(section.get("retain_status", True)),
            use_tls=_env_bool("MQTT_USE_TLS", bool(section.get("use_tls", False))),
            username=username,
            password=password,
            keepalive_s=int(os.getenv("MQTT_KEEPALIVE_S", "60")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.broker_host.strip():
            raise ValueError("MQTT broker host must not be empty")
        if not 1 <= self.broker_port <= 65535:
            raise ValueError("MQTT broker port must be between 1 and 65535")
        if self.qos != 1:
            raise ValueError("this telemetry contract requires MQTT QoS 1")
        if not self.topic_prefix.strip() or any(
            char in self.topic_prefix for char in "+#"
        ):
            raise ValueError(
                "MQTT topic prefix must be non-empty and cannot contain wildcards"
            )
        if self.keepalive_s <= 0:
            raise ValueError("MQTT keepalive must be positive")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _timestamp(value: datetime | None = None) -> str:
    stamp = value or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return (
        stamp.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )


class MqttPublisher:
    """Publish Phase 5 MQTT messages for one device."""

    def __init__(self, settings: MqttSettings, client: Any | None = None) -> None:
        settings.validate()
        self.settings = settings
        self.client = client or mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.client_id,
            protocol=mqtt.MQTTv311,
        )
        self.device_id: str | None = None
        self.sample_rate_hz = 0
        self.last_sequence = 0
        self._connected = False
        self._started_at = 0.0
        self._last_heartbeat = 0.0
        self._last_status = "NORMAL"

    def connect(self, device_id: str, sample_rate_hz: int) -> None:
        """Connect and publish retained online status with an offline LWT."""
        self._validate_device_id(device_id)
        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        self.device_id = device_id
        self.sample_rate_hz = sample_rate_hz
        will = {
            "device_id": device_id,
            "timestamp": _timestamp(),
            "online": False,
            "errors": [],
        }
        status_topic = self._topic(device_id, "status")
        self.client.will_set(status_topic, json.dumps(will), qos=1, retain=True)
        if self.settings.username:
            self.client.username_pw_set(self.settings.username, self.settings.password)
        if self.settings.use_tls:
            self.client.tls_set()
        result = self.client.connect(
            self.settings.broker_host,
            self.settings.broker_port,
            self.settings.keepalive_s,
        )
        if result not in (None, mqtt.MQTT_ERR_SUCCESS):
            raise ConnectionError(f"MQTT connect returned error code {result}")
        self.client.loop_start()
        self._connected = True
        self._started_at = time.monotonic()
        self._last_heartbeat = self._started_at
        self.publish_status(online=True)

    def publish_status(self, online: bool) -> None:
        """Publish retained status for dashboard last-known state."""
        device_id = self._require_device()
        uptime = (
            max(0, int(time.monotonic() - self._started_at)) if self._started_at else 0
        )
        payload = {
            "device_id": device_id,
            "timestamp": _timestamp(),
            "online": online,
            "firmware_version": "0.0.0-sim",
            "uptime_s": uptime,
            "sample_rate_hz": self.sample_rate_hz,
            "last_sequence": self.last_sequence,
            "wifi_rssi": None,
            "errors": [],
        }
        self._publish(
            self._topic(device_id, "status"),
            payload,
            retain=self.settings.retain_status,
        )
        self._last_heartbeat = time.monotonic()

    def publish_telemetry(
        self,
        features: FeatureVector,
        anomaly: AnomalyResult,
        sequence: int,
        source: str = "simulator",
    ) -> None:
        """Publish one feature vector and emit an alert on status transition."""
        device_id = self._require_device()
        if features.device_id != device_id:
            raise ValueError("feature device_id does not match connected device")
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        if source not in {"simulator", "hardware"}:
            raise ValueError("source must be 'simulator' or 'hardware'")
        if anomaly.status not in {"NORMAL", "WARNING", "CRITICAL"}:
            raise ValueError("unsupported machine status")
        if (
            not math.isfinite(anomaly.anomaly_score)
            or not 0.0 <= anomaly.anomaly_score <= 1.0
        ):
            raise ValueError("anomaly_score must be finite and between 0.0 and 1.0")

        payload = {
            "device_id": device_id,
            "timestamp": _timestamp(features.timestamp),
            "sequence": sequence,
            "source": source,
            "temperature_c": features.temperature_c,
            "vibration": {
                "x": features.vibration_x,
                "y": features.vibration_y,
                "z": features.vibration_z,
                "rms": features.vibration_rms,
                "peak": features.vibration_peak,
                "peak_to_peak": features.vibration_peak_to_peak,
                "std_dev": features.vibration_std,
                "crest_factor": features.crest_factor,
                "dominant_frequency_hz": features.dominant_frequency_hz,
            },
            "machine_status": anomaly.status,
            "anomaly_score": anomaly.anomaly_score,
            "triggered_rules": anomaly.triggered_rules,
        }
        self._publish(self._topic(device_id, "telemetry"), payload, retain=False)
        self.last_sequence = sequence

        now = time.monotonic()
        if now - self._last_heartbeat >= 60.0:
            self.publish_status(online=True)
        if anomaly.status != self._last_status:
            self.publish_alert(self._last_status, anomaly, features)
            self._last_status = anomaly.status

    def publish_alert(
        self,
        previous_status: str,
        anomaly: AnomalyResult,
        features: FeatureVector,
    ) -> None:
        """Publish a structured alert for a machine status transition."""
        device_id = self._require_device()
        payload = {
            "device_id": device_id,
            "timestamp": _timestamp(features.timestamp),
            "alert_id": str(uuid.uuid4()),
            "severity": anomaly.status,
            "previous_status": previous_status,
            "current_status": anomaly.status,
            "anomaly_score": anomaly.anomaly_score,
            "triggered_rules": anomaly.triggered_rules,
            "explanation": anomaly.explanation,
            "features": {
                "vibration_rms": features.vibration_rms,
                "crest_factor": features.crest_factor,
                "temperature_c": features.temperature_c,
                "dominant_frequency_hz": features.dominant_frequency_hz,
            },
        }
        self._publish(self._topic(device_id, "alerts"), payload, retain=False)

    def close(self) -> None:
        """Publish a graceful offline status and disconnect the client."""
        if not self._connected:
            return
        try:
            self.publish_status(online=False)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False

    def _publish(self, topic: str, payload: dict[str, Any], retain: bool) -> None:
        if not self._connected:
            raise ConnectionError("MQTT publisher is not connected")
        info = self.client.publish(
            topic,
            json.dumps(payload, separators=(",", ":"), allow_nan=False),
            qos=self.settings.qos,
            retain=retain,
        )
        if getattr(info, "rc", mqtt.MQTT_ERR_SUCCESS) != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with error code {info.rc}")
        if hasattr(info, "wait_for_publish"):
            info.wait_for_publish(timeout=5)
            if hasattr(info, "is_published") and not info.is_published():
                raise TimeoutError(f"MQTT publish timed out for {topic}")

    def _topic(self, device_id: str, suffix: str) -> str:
        return f"{self.settings.topic_prefix}/{device_id}/{suffix}"

    def _require_device(self) -> str:
        if not self._connected or self.device_id is None:
            raise ConnectionError("MQTT publisher is not connected")
        return self.device_id

    @staticmethod
    def _validate_device_id(device_id: str) -> None:
        if not device_id or any(char in device_id for char in "/+#"):
            raise ValueError("device_id must be a non-empty MQTT topic segment")
