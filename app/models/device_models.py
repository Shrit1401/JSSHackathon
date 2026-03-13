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
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH"]
    traffic_rate: float
    status: str
    last_seen: str


class DeviceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: int
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH"]
    traffic_rate: float
    status: str
    last_seen: str
    created_at: str
    open_ports: List[str]
    protocol_usage: Dict[str, float]
    security_explanation: str


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
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH"]
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


class AddDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    device_type: str
    ip_address: str
    vendor: str
    trust_score: int
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH"]
    traffic_rate: float
    status: str
    last_seen: str
    created_at: str


class SimulateAttackRequest(BaseModel):
    device_id: str
    attack_type: Optional[str] = None


class SimulateAttackResponse(BaseModel):
    device_id: str
    attack_type: str
    old_trust_score: int
    new_trust_score: int
    old_risk_level: str
    new_risk_level: str
    alert_created: bool
    message: str


class ExplainResponse(BaseModel):
    device_id: str
    device_name: str
    risk_level: Literal["SAFE", "LOW", "MEDIUM", "HIGH"]
    trust_score: int
    explanation: str
