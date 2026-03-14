from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType


class AlertType(str, Enum):
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ML_ANOMALY = "ML_ANOMALY"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    DRIFT_CONFIRMED = "DRIFT_CONFIRMED"
    TRUST_DROP = "TRUST_DROP"
    DEVICE_QUARANTINED = "DEVICE_QUARANTINED"
    POISONING_ATTEMPT = "POISONING_ATTEMPT"
    ATTACK_DETECTED = "ATTACK_DETECTED"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Alert(BaseModel):
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    device_id: str
    device_type: DeviceType
    title: str
    reason: str
    evidence: dict
    trust_score_at_time: Optional[float] = None
    timestamp: datetime
    acknowledged: bool = False


class AlertSummary(BaseModel):
    total_alerts: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
    by_device: dict[str, int]
    unacknowledged: int
    most_recent: Optional[datetime] = None
