from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType


class GateDecision(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    QUARANTINED = "quarantined"


class ProtectionStatus(str, Enum):
    LEARNING = "learning"
    FROZEN = "frozen"
    QUARANTINED = "quarantined"


class GateEvent(BaseModel):
    device_id: str
    device_type: DeviceType
    decision: GateDecision
    trust_score: float
    threshold: float
    reason: str
    timestamp: datetime


class PoisoningAttempt(BaseModel):
    device_id: str
    device_type: DeviceType
    trust_score_at_time: float
    protection_status: ProtectionStatus
    feature_drift_detected: bool
    reason: str
    timestamp: datetime


class DeviceProtectionState(BaseModel):
    device_id: str
    device_type: DeviceType
    status: ProtectionStatus
    is_frozen: bool
    is_quarantined: bool
    trust_score: float
    consecutive_denied: int
    total_allowed: int
    total_denied: int
    poisoning_attempts: int
    baseline_integrity: float
    last_allowed_update: Optional[datetime] = None
    last_decision: Optional[GateDecision] = None
    last_decision_time: Optional[datetime] = None


class ProtectionSummary(BaseModel):
    total_devices: int
    devices_learning: int
    devices_frozen: int
    devices_quarantined: int
    total_gate_events: int
    total_allowed: int
    total_denied: int
    total_poisoning_attempts: int
    average_integrity: float
    quarantine_threshold: int
    trust_gate_threshold: float
