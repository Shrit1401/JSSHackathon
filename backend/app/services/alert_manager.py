import uuid
from datetime import datetime
from collections import defaultdict
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.alerts import Alert, AlertType, AlertSeverity, AlertSummary
from app.services.drift_detector import DriftDetector
from app.services.policy_engine import PolicyEngine
from app.services.ml_detector import MLDetector
from app.services.trust_engine import TrustEngine
from app.models.policy import Confidence
from app.models.drift import DriftSeverity

DRIFT_TO_ALERT_SEVERITY = {
    DriftSeverity.LOW: AlertSeverity.LOW,
    DriftSeverity.MEDIUM: AlertSeverity.MEDIUM,
    DriftSeverity.HIGH: AlertSeverity.HIGH,
    DriftSeverity.CRITICAL: AlertSeverity.CRITICAL,
}

CONFIDENCE_TO_SEVERITY = {
    Confidence.LOW: AlertSeverity.LOW,
    Confidence.MEDIUM: AlertSeverity.MEDIUM,
    Confidence.HIGH: AlertSeverity.HIGH,
}


class AlertManager:
    def __init__(
        self,
        drift_detector: DriftDetector,
        policy_engine: PolicyEngine,
        ml_detector: MLDetector,
        trust_engine: TrustEngine,
    ):
        self.drift_detector = drift_detector
        self.policy_engine = policy_engine
        self.ml_detector = ml_detector
        self.trust_engine = trust_engine
        self.alerts: list[Alert] = []
        self._seen_keys: set[str] = set()

    def _add(self, alert: Alert):
        key = f"{alert.alert_type}:{alert.device_id}:{alert.reason[:50]}"
        if key not in self._seen_keys:
            self._seen_keys.add(key)
            self.alerts.append(alert)

    def scan_policy_violations(self):
        for violation in self.policy_engine.violations:
            self._add(Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=AlertType.POLICY_VIOLATION,
                severity=CONFIDENCE_TO_SEVERITY.get(violation.confidence, AlertSeverity.MEDIUM),
                device_id=violation.device_id,
                device_type=violation.device_type,
                title=f"Policy violation: {violation.rule_id}",
                reason=violation.description,
                evidence={
                    "rule_id": violation.rule_id,
                    "policy_type": violation.policy_type.value,
                    "evidence": violation.evidence,
                },
                timestamp=violation.timestamp,
            ))

    def scan_ml_anomalies(self):
        for score in self.ml_detector.get_anomalous_devices():
            severity = AlertSeverity.HIGH if score.anomaly_score >= 0.8 else AlertSeverity.MEDIUM
            top_contrib = max(score.feature_contributions, key=score.feature_contributions.get) if score.feature_contributions else "unknown"
            self._add(Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=AlertType.ML_ANOMALY,
                severity=severity,
                device_id=score.device_id,
                device_type=score.device_type,
                title=f"ML anomaly detected (score: {score.anomaly_score:.2f})",
                reason=f"Isolation Forest flagged {score.device_id} with anomaly score {score.anomaly_score:.2f}, top contributing feature: {top_contrib}",
                evidence={
                    "anomaly_score": score.anomaly_score,
                    "raw_score": score.raw_score,
                    "threshold": score.threshold,
                    "feature_contributions": score.feature_contributions,
                },
                timestamp=score.timestamp,
            ))

    def scan_drift_events(self):
        for event in self.drift_detector.events:
            if event.event_type in ("drift_confirmed", "severity_escalated"):
                self._add(Alert(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.DRIFT_CONFIRMED if event.event_type == "drift_confirmed" else AlertType.DRIFT_DETECTED,
                    severity=DRIFT_TO_ALERT_SEVERITY.get(event.severity, AlertSeverity.MEDIUM),
                    device_id=event.device_id,
                    device_type=event.device_type,
                    title=f"Behavioral drift {event.event_type.replace('_', ' ')}",
                    reason=event.description,
                    evidence={
                        "drift_score": event.drift_score,
                        "drifting_features": event.drifting_features,
                        "window_id": event.window_id,
                    },
                    timestamp=event.timestamp,
                ))

    def scan_trust_drops(self):
        for score in self.trust_engine.get_all_latest():
            if score.trust_score < 40:
                severity = AlertSeverity.CRITICAL
            elif score.trust_score < 60:
                severity = AlertSeverity.HIGH
            else:
                continue

            self._add(Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=AlertType.TRUST_DROP,
                severity=severity,
                device_id=score.device_id,
                device_type=score.device_type,
                title=f"Trust score critically low: {score.trust_score:.1f}",
                reason=f"{score.device_id} trust dropped to {score.trust_score:.1f} ({score.risk_level.value} risk)",
                evidence={
                    "trust_score": score.trust_score,
                    "risk_level": score.risk_level.value,
                    "breakdown": score.signal_breakdown.model_dump(),
                },
                trust_score_at_time=score.trust_score,
                timestamp=score.timestamp,
            ))

    def scan_quarantine_events(self):
        for state in self.trust_engine.protector.get_quarantined_devices():
            self._add(Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=AlertType.DEVICE_QUARANTINED,
                severity=AlertSeverity.CRITICAL,
                device_id=state.device_id,
                device_type=state.device_type,
                title=f"Device quarantined: {state.device_id}",
                reason=f"{state.device_id} quarantined after {state.consecutive_denied} consecutive baseline denials",
                evidence={
                    "consecutive_denied": state.consecutive_denied,
                    "poisoning_attempts": state.poisoning_attempts,
                    "baseline_integrity": state.baseline_integrity,
                },
                trust_score_at_time=state.trust_score,
                timestamp=state.last_decision_time or datetime.utcnow(),
            ))

    def scan_poisoning_attempts(self):
        for attempt in self.trust_engine.protector.poisoning_attempts:
            self._add(Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=AlertType.POISONING_ATTEMPT,
                severity=AlertSeverity.HIGH,
                device_id=attempt.device_id,
                device_type=attempt.device_type,
                title=f"Baseline poisoning attempt: {attempt.device_id}",
                reason=attempt.reason,
                evidence={
                    "trust_score": attempt.trust_score_at_time,
                    "drift_detected": attempt.feature_drift_detected,
                    "protection_status": attempt.protection_status.value,
                },
                trust_score_at_time=attempt.trust_score_at_time,
                timestamp=attempt.timestamp,
            ))

    def scan_all(self):
        self.scan_policy_violations()
        self.scan_ml_anomalies()
        self.scan_drift_events()
        self.scan_trust_drops()
        self.scan_quarantine_events()
        self.scan_poisoning_attempts()

    def get_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        device_id: Optional[str] = None,
    ) -> list[Alert]:
        result = self.alerts
        if alert_type:
            result = [a for a in result if a.alert_type == alert_type]
        if severity:
            result = [a for a in result if a.severity == severity]
        if device_id:
            result = [a for a in result if a.device_id == device_id]
        return sorted(result, key=lambda a: a.timestamp, reverse=True)

    def acknowledge(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_summary(self) -> AlertSummary:
        by_type: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        by_device: dict[str, int] = defaultdict(int)
        unack = 0

        for a in self.alerts:
            by_type[a.alert_type.value] += 1
            by_severity[a.severity.value] += 1
            by_device[a.device_id] += 1
            if not a.acknowledged:
                unack += 1

        most_recent = max((a.timestamp for a in self.alerts), default=None)

        return AlertSummary(
            total_alerts=len(self.alerts),
            by_type=dict(by_type),
            by_severity=dict(by_severity),
            by_device=dict(by_device),
            unacknowledged=unack,
            most_recent=most_recent,
        )
