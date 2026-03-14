from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict


class DeviceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: int
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]
    traffic_rate: float
    status: str
    last_seen: str


class SignalBreakdownOut(BaseModel):
    ml_anomaly_score: float = 0.0
    ml_penalty: float = 0.0
    drift_score: float = 0.0
    drift_penalty: float = 0.0
    drift_confirmed: bool = False
    drift_confirmation_penalty: float = 0.0
    policy_violations_total: int = 0
    policy_high_confidence: int = 0
    policy_penalty: float = 0.0
    total_penalty: float = 0.0
    baseline_update_allowed: bool = True


class DeviceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: int
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]
    traffic_rate: float
    status: str
    last_seen: str
    created_at: str
    open_ports: List[str]
    protocol_usage: Dict[str, float]
    security_explanation: str
    signal_breakdown: Optional[SignalBreakdownOut] = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    timestamp: str


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    timestamp: str


class OverviewStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_devices: int
    safe: int
    low: int
    medium: int
    high: int
    online: int
    offline: int


class NetworkNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]
    trust_score: int
    status: str


class NetworkEdge(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    target: str


class NetworkMap(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nodes: List[NetworkNode]
    edges: List[NetworkEdge]


class AddDeviceRequest(BaseModel):
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: Optional[int] = 100
    traffic_rate: Optional[float] = 0.0
    status: Optional[str] = "online"
    parent_id: Optional[str] = None


class AddDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: int
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]
    traffic_rate: float
    status: str
    last_seen: str
    created_at: str
    parent_id: Optional[str] = None


class SimulateAttackRequest(BaseModel):
    device_id: str
    attack_type: Optional[str] = None
    stealth_level: Optional[Literal["low", "medium", "high"]] = "medium"


class SimulateAttackResponse(BaseModel):
    device_id: str
    attack_type: str
    old_trust_score: int
    new_trust_score: int
    old_risk_level: str
    new_risk_level: str
    alert_created: bool
    message: str
    detection_difficulty: Optional[int] = None


class ExplainResponse(BaseModel):
    device_id: str
    device_name: str
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]
    trust_score: int
    explanation: str
    signal_breakdown: Optional[SignalBreakdownOut] = None
