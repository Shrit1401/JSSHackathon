from datetime import datetime
from collections import defaultdict
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.features import DeviceFeatureVector
from app.models.protection import (
    GateDecision,
    ProtectionStatus,
    GateEvent,
    PoisoningAttempt,
    DeviceProtectionState,
    ProtectionSummary,
)
from app.services.baseline_engine import BaselineEngine

TRUST_GATE_THRESHOLD = 85.0
QUARANTINE_AFTER_DENIALS = 5


class BaselineProtector:
    def __init__(self, baseline_engine: BaselineEngine):
        self.baseline_engine = baseline_engine
        self.gate_events: list[GateEvent] = []
        self.poisoning_attempts: list[PoisoningAttempt] = []
        self._consecutive_denied: dict[str, int] = defaultdict(int)
        self._total_allowed: dict[str, int] = defaultdict(int)
        self._total_denied: dict[str, int] = defaultdict(int)
        self._poisoning_count: dict[str, int] = defaultdict(int)
        self._quarantined: set[str] = set()
        self._last_allowed_time: dict[str, datetime] = {}
        self._device_types: dict[str, DeviceType] = {}

    def gate_check(
        self,
        device_id: str,
        device_type: DeviceType,
        trust_score: float,
        feature_vector: Optional[DeviceFeatureVector] = None,
    ) -> GateDecision:
        self._device_types[device_id] = device_type
        now = datetime.utcnow()

        if device_id in self._quarantined:
            decision = GateDecision.QUARANTINED
            reason = f"Device quarantined after {QUARANTINE_AFTER_DENIALS}+ consecutive denials — manual review required"
            self._log_gate_event(device_id, device_type, decision, trust_score, reason, now)
            self._record_poisoning(device_id, device_type, trust_score, ProtectionStatus.QUARANTINED, feature_vector, reason)
            return decision

        if trust_score >= TRUST_GATE_THRESHOLD:
            decision = GateDecision.ALLOWED
            reason = f"Trust {trust_score:.1f} >= {TRUST_GATE_THRESHOLD} — baseline update permitted"
            self._consecutive_denied[device_id] = 0
            self._total_allowed[device_id] += 1
            self._last_allowed_time[device_id] = now
            self.baseline_engine.unfreeze_device(device_id)
            self._log_gate_event(device_id, device_type, decision, trust_score, reason, now)
            return decision

        self._consecutive_denied[device_id] += 1
        self._total_denied[device_id] += 1
        self.baseline_engine.freeze_device(device_id)

        has_drift = False
        if feature_vector:
            try:
                dev = self.baseline_engine.compute_deviation(feature_vector)
                has_drift = len(dev.features_beyond_threshold) > 0
            except ValueError:
                pass

        if has_drift:
            self._record_poisoning(
                device_id, device_type, trust_score,
                ProtectionStatus.FROZEN, feature_vector,
                f"Baseline update blocked while device shows anomalous drift (trust={trust_score:.1f})"
            )

        if self._consecutive_denied[device_id] >= QUARANTINE_AFTER_DENIALS:
            self._quarantined.add(device_id)
            decision = GateDecision.QUARANTINED
            reason = (
                f"Trust {trust_score:.1f} < {TRUST_GATE_THRESHOLD} for "
                f"{self._consecutive_denied[device_id]} consecutive cycles — ESCALATED TO QUARANTINE"
            )
        else:
            decision = GateDecision.DENIED
            reason = (
                f"Trust {trust_score:.1f} < {TRUST_GATE_THRESHOLD} — "
                f"baseline frozen (denial streak: {self._consecutive_denied[device_id]}/{QUARANTINE_AFTER_DENIALS})"
            )

        self._log_gate_event(device_id, device_type, decision, trust_score, reason, now)
        return decision

    def try_update_baseline(
        self,
        device_id: str,
        device_type: DeviceType,
        trust_score: float,
        feature_vector: DeviceFeatureVector,
    ) -> bool:
        decision = self.gate_check(device_id, device_type, trust_score, feature_vector)
        if decision == GateDecision.ALLOWED:
            return self.baseline_engine.update_device_baseline(device_id, feature_vector)
        return False

    def lift_quarantine(self, device_id: str) -> bool:
        if device_id not in self._quarantined:
            return False
        self._quarantined.discard(device_id)
        self._consecutive_denied[device_id] = 0
        return True

    def _log_gate_event(
        self, device_id: str, device_type: DeviceType,
        decision: GateDecision, trust_score: float,
        reason: str, timestamp: datetime,
    ):
        self.gate_events.append(GateEvent(
            device_id=device_id,
            device_type=device_type,
            decision=decision,
            trust_score=trust_score,
            threshold=TRUST_GATE_THRESHOLD,
            reason=reason,
            timestamp=timestamp,
        ))

    def _record_poisoning(
        self, device_id: str, device_type: DeviceType,
        trust_score: float, status: ProtectionStatus,
        feature_vector: Optional[DeviceFeatureVector],
        reason: str,
    ):
        has_drift = False
        if feature_vector:
            try:
                dev = self.baseline_engine.compute_deviation(feature_vector)
                has_drift = len(dev.features_beyond_threshold) > 0
            except ValueError:
                pass

        self._poisoning_count[device_id] += 1
        self.poisoning_attempts.append(PoisoningAttempt(
            device_id=device_id,
            device_type=device_type,
            trust_score_at_time=trust_score,
            protection_status=status,
            feature_drift_detected=has_drift,
            reason=reason,
            timestamp=datetime.utcnow(),
        ))

    def get_device_state(self, device_id: str) -> Optional[DeviceProtectionState]:
        device_type = self._device_types.get(device_id)
        if not device_type:
            return None

        baseline = self.baseline_engine.get_device_baseline(device_id)
        is_frozen = baseline.is_frozen if baseline else False
        is_quarantined = device_id in self._quarantined

        if is_quarantined:
            status = ProtectionStatus.QUARANTINED
        elif is_frozen:
            status = ProtectionStatus.FROZEN
        else:
            status = ProtectionStatus.LEARNING

        allowed = self._total_allowed.get(device_id, 0)
        denied = self._total_denied.get(device_id, 0)
        total = allowed + denied
        integrity = round(allowed / total, 4) if total > 0 else 1.0

        device_events = [e for e in self.gate_events if e.device_id == device_id]
        last_event = device_events[-1] if device_events else None

        trust = last_event.trust_score if last_event else 100.0

        return DeviceProtectionState(
            device_id=device_id,
            device_type=device_type,
            status=status,
            is_frozen=is_frozen,
            is_quarantined=is_quarantined,
            trust_score=trust,
            consecutive_denied=self._consecutive_denied.get(device_id, 0),
            total_allowed=allowed,
            total_denied=denied,
            poisoning_attempts=self._poisoning_count.get(device_id, 0),
            baseline_integrity=integrity,
            last_allowed_update=self._last_allowed_time.get(device_id),
            last_decision=last_event.decision if last_event else None,
            last_decision_time=last_event.timestamp if last_event else None,
        )

    def get_all_device_states(self) -> list[DeviceProtectionState]:
        states = []
        for device_id in self._device_types:
            state = self.get_device_state(device_id)
            if state:
                states.append(state)
        return sorted(states, key=lambda s: s.baseline_integrity)

    def get_quarantined_devices(self) -> list[DeviceProtectionState]:
        return [s for s in self.get_all_device_states() if s.is_quarantined]

    def get_gate_events(
        self,
        device_id: Optional[str] = None,
        decision: Optional[GateDecision] = None,
    ) -> list[GateEvent]:
        events = self.gate_events
        if device_id:
            events = [e for e in events if e.device_id == device_id]
        if decision:
            events = [e for e in events if e.decision == decision]
        return events

    def get_poisoning_attempts(self, device_id: Optional[str] = None) -> list[PoisoningAttempt]:
        attempts = self.poisoning_attempts
        if device_id:
            attempts = [a for a in attempts if a.device_id == device_id]
        return attempts

    def get_summary(self) -> ProtectionSummary:
        states = self.get_all_device_states()
        learning = sum(1 for s in states if s.status == ProtectionStatus.LEARNING)
        frozen = sum(1 for s in states if s.status == ProtectionStatus.FROZEN)
        quarantined = sum(1 for s in states if s.status == ProtectionStatus.QUARANTINED)

        integrities = [s.baseline_integrity for s in states]
        avg_integrity = round(sum(integrities) / max(len(integrities), 1), 4)

        return ProtectionSummary(
            total_devices=len(states),
            devices_learning=learning,
            devices_frozen=frozen,
            devices_quarantined=quarantined,
            total_gate_events=len(self.gate_events),
            total_allowed=sum(self._total_allowed.values()),
            total_denied=sum(self._total_denied.values()),
            total_poisoning_attempts=len(self.poisoning_attempts),
            average_integrity=avg_integrity,
            quarantine_threshold=QUARANTINE_AFTER_DENIALS,
            trust_gate_threshold=TRUST_GATE_THRESHOLD,
        )
