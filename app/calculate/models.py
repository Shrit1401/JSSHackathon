from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Telemetry ──

class DeviceType(str, Enum):
    CAMERA = "camera"
    PRINTER = "printer"
    ROUTER = "router"
    LAPTOP = "laptop"
    SMART_TV = "smart_tv"
    THERMOSTAT = "thermostat"
    SMART_DOOR_LOCK = "smart_door_lock"
    SMART_LIGHT_HUB = "smart_light_hub"
    TEMPERATURE_SENSOR = "temperature_sensor"
    NETWORK_GATEWAY = "network_gateway"


class Protocol(str, Enum):
    RTSP = "RTSP"
    HTTPS = "HTTPS"
    HTTP = "HTTP"
    DNS = "DNS"
    NTP = "NTP"
    SSH = "SSH"
    TELNET = "Telnet"
    FTP = "FTP"
    IPP = "IPP"
    MDNS = "mDNS"
    DHCP = "DHCP"
    QUIC = "QUIC"
    UDP = "UDP"
    TCP = "TCP"
    WEBSOCKET = "WebSocket"
    GIT = "Git"
    MQTT = "MQTT"
    COAP = "CoAP"
    ZIGBEE = "Zigbee"
    BLUETOOTH = "BLE"


class DestinationType(str, Enum):
    INTERNAL = "internal"
    TRUSTED_CLOUD = "trusted_cloud"
    UNKNOWN_EXTERNAL = "unknown_external"


class TelemetryRecord(BaseModel):
    record_id: str
    device_id: str
    device_type: DeviceType
    src_ip: str
    dst_ip: str
    protocol: Protocol
    bytes_sent: int = Field(ge=0)
    bytes_received: int = Field(ge=0)
    session_duration: float = Field(ge=0, description="Duration in seconds")
    packet_count: int = Field(ge=0)
    destination_type: DestinationType
    timestamp: datetime
    window_id: Optional[int] = None


class DeviceState(BaseModel):
    device_id: str
    device_type: DeviceType
    ip_address: str
    is_compromised: bool = False
    active_attack: Optional[str] = None
    last_seen: Optional[datetime] = None
    total_records: int = 0


# ── Features ──

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


class FeatureSummary(BaseModel):
    total_devices: int
    total_windows: int
    features_computed: int
    feature_names: list[str]


# ── Baseline ──

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


# ── Drift ──

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


# ── Policy ──

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


# ── ML ──

class AnomalyScore(BaseModel):
    device_id: str
    device_type: DeviceType
    window_id: int
    anomaly_score: float
    raw_score: float
    is_anomalous: bool
    threshold: float
    feature_contributions: dict[str, float]
    timestamp: datetime


class MLModelInfo(BaseModel):
    model_type: str
    training_samples: int
    training_features: list[str]
    contamination: float
    trained_at: Optional[datetime] = None
    dataset_source: str
    benign_samples: int
    malicious_samples: int


class MLSummary(BaseModel):
    model_loaded: bool
    model_info: Optional[MLModelInfo] = None
    total_scored: int
    anomalies_detected: int
    anomaly_rate: float


# ── Trust ──

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


# ── Alerts ──

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


# ── Protection ──

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
