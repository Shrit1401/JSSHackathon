from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType, Protocol, DestinationType


class PolicyType(str, Enum):
    PROTOCOL_BLACKLIST = "protocol_blacklist"
    DESTINATION_RESTRICTION = "destination_restriction"
    TRAFFIC_CEILING = "traffic_ceiling"
    SESSION_LIMIT = "session_limit"
    TRAFFIC_DIRECTION = "traffic_direction"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PolicyRule(BaseModel):
    rule_id: str
    policy_type: PolicyType
    device_type: DeviceType
    description: str
    confidence: Confidence
    parameters: dict


class PolicyViolation(BaseModel):
    violation_id: str
    rule_id: str
    policy_type: PolicyType
    device_id: str
    device_type: DeviceType
    confidence: Confidence
    description: str
    evidence: dict
    record_id: str
    timestamp: datetime


class RecordEvaluation(BaseModel):
    record_id: str
    device_id: str
    device_type: DeviceType
    rules_checked: int
    violations_found: int
    violations: list[PolicyViolation]
    is_compliant: bool


class DevicePolicyState(BaseModel):
    device_id: str
    device_type: DeviceType
    total_records_evaluated: int
    total_violations: int
    violations_by_type: dict[str, int]
    violation_rate: float
    last_violation: Optional[datetime] = None
    is_compliant: bool


class PolicySummary(BaseModel):
    total_rules: int
    rules_by_type: dict[str, int]
    rules_by_device_type: dict[str, int]
    total_violations: int
    devices_with_violations: int
    total_records_evaluated: int
