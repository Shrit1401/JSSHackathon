from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.telemetry import DeviceType


class DeviceFeatureVector(BaseModel):
    device_id: str
    device_type: DeviceType
    window_id: int

    packet_rate: float
    avg_session_duration: float
    total_bytes_sent: int
    total_bytes_received: int
    traffic_volume: int

    unique_destinations: int
    destination_entropy: float

    unique_protocols: int
    protocol_entropy: float
    protocol_distribution: dict[str, float]

    external_connection_ratio: float
    inbound_outbound_ratio: float

    record_count: int
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None


class DeviceFeatureTimeline(BaseModel):
    device_id: str
    device_type: DeviceType
    windows: list[DeviceFeatureVector]
    total_windows: int


class FeatureSummary(BaseModel):
    total_devices: int
    total_windows: int
    features_computed: int
    feature_names: list[str]
