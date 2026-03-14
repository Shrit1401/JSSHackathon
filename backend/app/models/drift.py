from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType


class DriftSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureDrift(BaseModel):
    feature_name: str
    z_score: float
    abs_z_score: float
    baseline_mean: float
    baseline_std: float
    current_value: float
    is_drifting: bool
    consecutive_windows: int


class DriftResult(BaseModel):
    device_id: str
    device_type: DeviceType
    window_id: int
    timestamp: datetime

    is_drifting: bool
    severity: DriftSeverity
    drift_score: float
    consecutive_drift_windows: int

    drifting_features: list[FeatureDrift]
    top_drifting_feature: Optional[str] = None
    top_z_score: float = 0.0

    total_features_checked: int
    features_beyond_threshold: int


class DeviceDriftState(BaseModel):
    device_id: str
    device_type: DeviceType

    current_severity: DriftSeverity
    is_drifting: bool
    consecutive_drift_windows: int
    max_consecutive_drift: int
    total_drift_windows: int
    total_windows_analyzed: int

    latest_drift_score: float
    peak_drift_score: float

    currently_drifting_features: list[str]
    historically_drifted_features: list[str]

    first_drift_detected: Optional[datetime] = None
    last_drift_detected: Optional[datetime] = None
    drift_confirmed_at: Optional[datetime] = None


class DriftEvent(BaseModel):
    event_id: str
    device_id: str
    device_type: DeviceType
    event_type: str
    severity: DriftSeverity
    drift_score: float
    window_id: int
    timestamp: datetime
    drifting_features: list[str]
    description: str


class DriftSummary(BaseModel):
    total_devices_monitored: int
    devices_currently_drifting: int
    devices_by_severity: dict[str, int]
    total_drift_events: int
    confirmation_windows: int
    z_score_threshold: float
