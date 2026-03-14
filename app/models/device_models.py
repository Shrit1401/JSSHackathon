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


class FeatureVectorOut(BaseModel):
    packet_rate: float = 0.0
    avg_session_duration: float = 0.0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    traffic_volume: int = 0
    unique_destinations: int = 0
    destination_entropy: float = 0.0
    unique_protocols: int = 0
    protocol_entropy: float = 0.0
    protocol_distribution: Dict[str, float] = {}
    external_connection_ratio: float = 0.0
    inbound_outbound_ratio: float = 0.0
    record_count: int = 0
    window_start: Optional[str] = None
    window_end: Optional[str] = None


class FeatureStatOut(BaseModel):
    mean: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0
    samples: int = 0


class BaselineOut(BaseModel):
    windows_learned: int = 0
    is_frozen: bool = False
    last_updated: Optional[str] = None
    allowed_protocols: List[str] = []
    expected_destination_types: List[str] = []
    feature_stats: Dict[str, FeatureStatOut] = {}


class DriftingFeatureOut(BaseModel):
    feature: str
    z_score: float
    baseline_mean: float
    baseline_std: float
    current_value: float
    consecutive_windows: int = 0


class DriftStateOut(BaseModel):
    is_drifting: bool = False
    severity: str = "none"
    drift_score: float = 0.0
    peak_drift_score: float = 0.0
    consecutive_drift_windows: int = 0
    max_consecutive_drift: int = 0
    total_drift_windows: int = 0
    total_windows_analyzed: int = 0
    currently_drifting_features: List[str] = []
    historically_drifted_features: List[str] = []
    drifting_features_detail: List[DriftingFeatureOut] = []
    first_drift_detected: Optional[str] = None
    last_drift_detected: Optional[str] = None
    drift_confirmed_at: Optional[str] = None


class PolicyViolationOut(BaseModel):
    rule_id: str
    policy_type: str
    confidence: str
    description: str
    evidence: dict = {}
    timestamp: str


class PolicyStateOut(BaseModel):
    is_compliant: bool = True
    total_records_evaluated: int = 0
    total_violations: int = 0
    violation_rate: float = 0.0
    violations_by_type: Dict[str, int] = {}
    last_violation: Optional[str] = None
    recent_violations: List[PolicyViolationOut] = []


class MLAnomalyOut(BaseModel):
    anomaly_score: float = 0.0
    raw_score: float = 0.0
    is_anomalous: bool = False
    threshold: float = 0.5
    feature_contributions: Dict[str, float] = {}
    top_contributing_feature: Optional[str] = None
    total_scored: int = 0
    anomalous_count: int = 0
    score_history: List[dict] = []


class ProtectionStateOut(BaseModel):
    status: str = "learning"
    is_frozen: bool = False
    is_quarantined: bool = False
    trust_score: float = 100.0
    consecutive_denied: int = 0
    total_allowed: int = 0
    total_denied: int = 0
    poisoning_attempts: int = 0
    baseline_integrity: float = 1.0
    last_allowed_update: Optional[str] = None
    last_decision: Optional[str] = None
    last_decision_time: Optional[str] = None


class TrustHistoryPointOut(BaseModel):
    trust_score: float
    risk_level: str
    timestamp: str


class TrustHistoryOut(BaseModel):
    current_score: float = 100.0
    current_risk: str = "SAFE"
    lowest_score: float = 100.0
    highest_score: float = 100.0
    average_score: float = 100.0
    total_windows: int = 0
    trajectory: List[TrustHistoryPointOut] = []


class DeviceAnalyticsOut(BaseModel):
    trust_detail: Optional[SignalBreakdownOut] = None
    features: Optional[FeatureVectorOut] = None
    baseline: Optional[BaselineOut] = None
    drift: Optional[DriftStateOut] = None
    policy: Optional[PolicyStateOut] = None
    ml_anomaly: Optional[MLAnomalyOut] = None
    protection: Optional[ProtectionStateOut] = None
    trust_history: Optional[TrustHistoryOut] = None


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
    features: Optional[FeatureVectorOut] = None
    drift: Optional[DriftStateOut] = None
    policy: Optional[PolicyStateOut] = None
    ml_anomaly: Optional[MLAnomalyOut] = None
    protection: Optional[ProtectionStateOut] = None
    trust_history: Optional[TrustHistoryOut] = None


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


class MLModelInfoOut(BaseModel):
    model_type: str = "IsolationForest"
    training_samples: int = 0
    training_features: List[str] = []
    contamination: float = 0.01
    trained_at: Optional[str] = None
    dataset_source: str = ""
    benign_samples: int = 0
    malicious_samples: int = 0
    total_scored: int = 0
    anomalies_detected: int = 0
    anomaly_rate: float = 0.0
