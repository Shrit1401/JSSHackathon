from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.telemetry import DeviceType


class FeatureStats(BaseModel):
    mean: float
    std: float
    min_val: float
    max_val: float
    samples: int


class DeviceBaseline(BaseModel):
    device_id: str
    device_type: DeviceType
    is_frozen: bool = False
    windows_learned: int = 0
    last_updated: Optional[datetime] = None

    packet_rate: FeatureStats
    avg_session_duration: FeatureStats
    traffic_volume: FeatureStats
    total_bytes_sent: FeatureStats
    total_bytes_received: FeatureStats
    destination_entropy: FeatureStats
    protocol_entropy: FeatureStats
    unique_destinations: FeatureStats
    unique_protocols: FeatureStats
    external_connection_ratio: FeatureStats
    inbound_outbound_ratio: FeatureStats

    allowed_protocols: list[str]
    expected_destination_types: list[str]


class DeviceTypeBaseline(BaseModel):
    device_type: DeviceType
    device_count: int
    total_windows: int
    last_updated: Optional[datetime] = None

    packet_rate: FeatureStats
    avg_session_duration: FeatureStats
    traffic_volume: FeatureStats
    total_bytes_sent: FeatureStats
    total_bytes_received: FeatureStats
    destination_entropy: FeatureStats
    protocol_entropy: FeatureStats
    unique_destinations: FeatureStats
    unique_protocols: FeatureStats
    external_connection_ratio: FeatureStats
    inbound_outbound_ratio: FeatureStats

    allowed_protocols: list[str]
    expected_destination_types: list[str]
    traffic_direction: str


class BaselineDeviation(BaseModel):
    device_id: str
    device_type: DeviceType
    window_id: int
    deviations: dict[str, float]
    max_deviation_feature: str
    max_deviation_zscore: float
    features_beyond_threshold: list[str]
    threshold_used: float


class BaselineSummary(BaseModel):
    total_device_baselines: int
    total_type_baselines: int
    frozen_devices: int
    baseline_phase_windows: int
    device_types_covered: list[str]
