from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SignalBreakdown(BaseModel):
    ml_anomaly_score: float
    ml_penalty: float
    drift_score: float
    drift_normalized: float
    drift_penalty: float
    drift_confirmed: bool
    drift_confirmation_penalty: float
    policy_violations_total: int
    policy_high_confidence: int
    policy_penalty: float
    total_penalty: float


class DeviceTrustScore(BaseModel):
    device_id: str
    device_type: DeviceType
    trust_score: float
    risk_level: RiskLevel
    signal_breakdown: SignalBreakdown
    baseline_update_allowed: bool
    timestamp: datetime


class DeviceTrustHistory(BaseModel):
    device_id: str
    device_type: DeviceType
    scores: list[DeviceTrustScore]
    current_score: float
    current_risk: RiskLevel
    lowest_score: float
    highest_score: float
    average_score: float


class TrustSummary(BaseModel):
    total_devices: int
    devices_by_risk: dict[str, int]
    average_trust: float
    lowest_trust_device: Optional[str] = None
    lowest_trust_score: float = 100.0
    baseline_updates_blocked: int
    weights: dict[str, float]
