import uuid
from datetime import datetime
from collections import defaultdict
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.events import Event, EventCategory, EventSummary
from app.services.telemetry_generator import TelemetryGenerator
from app.services.drift_detector import DriftDetector
from app.services.policy_engine import PolicyEngine
from app.services.ml_detector import MLDetector
from app.services.trust_engine import TrustEngine


class EventTimeline:
    def __init__(
        self,
        generator: TelemetryGenerator,
        drift_detector: DriftDetector,
        policy_engine: PolicyEngine,
        ml_detector: MLDetector,
        trust_engine: TrustEngine,
    ):
        self.generator = generator
        self.drift_detector = drift_detector
        self.policy_engine = policy_engine
        self.ml_detector = ml_detector
        self.trust_engine = trust_engine
        self.custom_events: list[Event] = []

    def log_event(
        self,
        category: EventCategory,
        event_type: str,
        description: str,
        device_id: Optional[str] = None,
        device_type: Optional[DeviceType] = None,
        metadata: Optional[dict] = None,
    ) -> Event:
        event = Event(
            event_id=str(uuid.uuid4()),
            category=category,
            event_type=event_type,
            device_id=device_id,
            device_type=device_type,
            description=description,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
        )
        self.custom_events.append(event)
        return event

    def _collect_device_events(self) -> list[Event]:
        events = []
        for device in self.generator.devices:
            events.append(Event(
                event_id=str(uuid.uuid4()),
                category=EventCategory.SYSTEM,
                event_type="device_registered",
                device_id=device.device_id,
                device_type=device.device_type,
                description=f"{device.device_id} ({device.device_type.value}) registered with IP {device.ip_address}",
                metadata={"ip": device.ip_address, "total_records": device.total_records},
                timestamp=device.last_seen or datetime.utcnow(),
            ))

            if device.is_compromised:
                events.append(Event(
                    event_id=str(uuid.uuid4()),
                    category=EventCategory.ATTACK,
                    event_type="attack_active",
                    device_id=device.device_id,
                    device_type=device.device_type,
                    description=f"{device.device_id} under active attack: {device.active_attack}",
                    metadata={"attack_type": device.active_attack},
                    timestamp=device.last_seen or datetime.utcnow(),
                ))
        return events

    def _collect_drift_events(self) -> list[Event]:
        events = []
        for de in self.drift_detector.events:
            events.append(Event(
                event_id=de.event_id,
                category=EventCategory.DETECTION,
                event_type=f"drift_{de.event_type}",
                device_id=de.device_id,
                device_type=de.device_type,
                description=de.description,
                metadata={
                    "drift_score": de.drift_score,
                    "severity": de.severity.value,
                    "features": de.drifting_features,
                    "window_id": de.window_id,
                },
                timestamp=de.timestamp,
            ))
        return events

    def _collect_policy_events(self) -> list[Event]:
        events = []
        seen = set()
        for v in self.policy_engine.violations:
            key = f"{v.device_id}:{v.rule_id}"
            if key in seen:
                continue
            seen.add(key)
            events.append(Event(
                event_id=str(uuid.uuid4()),
                category=EventCategory.POLICY,
                event_type="policy_violation",
                device_id=v.device_id,
                device_type=v.device_type,
                description=v.description,
                metadata={
                    "rule_id": v.rule_id,
                    "policy_type": v.policy_type.value,
                    "confidence": v.confidence.value,
                    "evidence": v.evidence,
                },
                timestamp=v.timestamp,
            ))
        return events

    def _collect_trust_events(self) -> list[Event]:
        events = []
        for score in self.trust_engine.get_all_latest():
            if score.trust_score < 60:
                events.append(Event(
                    event_id=str(uuid.uuid4()),
                    category=EventCategory.TRUST,
                    event_type="trust_critical" if score.trust_score < 40 else "trust_warning",
                    device_id=score.device_id,
                    device_type=score.device_type,
                    description=f"{score.device_id} trust at {score.trust_score:.1f} ({score.risk_level.value})",
                    metadata={
                        "trust_score": score.trust_score,
                        "risk_level": score.risk_level.value,
                        "ml_penalty": score.signal_breakdown.ml_penalty,
                        "drift_penalty": score.signal_breakdown.drift_penalty,
                        "policy_penalty": score.signal_breakdown.policy_penalty,
                    },
                    timestamp=score.timestamp,
                ))
        return events

    def _collect_protection_events(self) -> list[Event]:
        events = []
        for ge in self.trust_engine.protector.gate_events:
            if ge.decision.value != "allowed":
                events.append(Event(
                    event_id=str(uuid.uuid4()),
                    category=EventCategory.PROTECTION,
                    event_type=f"baseline_{ge.decision.value}",
                    device_id=ge.device_id,
                    device_type=ge.device_type,
                    description=ge.reason,
                    metadata={
                        "decision": ge.decision.value,
                        "trust_score": ge.trust_score,
                        "threshold": ge.threshold,
                    },
                    timestamp=ge.timestamp,
                ))

        for pa in self.trust_engine.protector.poisoning_attempts:
            events.append(Event(
                event_id=str(uuid.uuid4()),
                category=EventCategory.PROTECTION,
                event_type="poisoning_attempt",
                device_id=pa.device_id,
                device_type=pa.device_type,
                description=pa.reason,
                metadata={
                    "trust_score": pa.trust_score_at_time,
                    "drift_detected": pa.feature_drift_detected,
                    "status": pa.protection_status.value,
                },
                timestamp=pa.timestamp,
            ))
        return events

    def get_timeline(
        self,
        category: Optional[EventCategory] = None,
        device_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 200,
    ) -> list[Event]:
        all_events = (
            self.custom_events
            + self._collect_device_events()
            + self._collect_drift_events()
            + self._collect_policy_events()
            + self._collect_trust_events()
            + self._collect_protection_events()
        )

        if category:
            all_events = [e for e in all_events if e.category == category]
        if device_id:
            all_events = [e for e in all_events if e.device_id == device_id]
        if event_type:
            all_events = [e for e in all_events if e.event_type == event_type]

        all_events.sort(key=lambda e: e.timestamp, reverse=True)
        return all_events[:limit]

    def get_device_timeline(self, device_id: str, limit: int = 100) -> list[Event]:
        return self.get_timeline(device_id=device_id, limit=limit)

    def get_summary(self) -> EventSummary:
        all_events = self.get_timeline(limit=10000)
        by_cat: dict[str, int] = defaultdict(int)
        by_dev: dict[str, int] = defaultdict(int)

        for e in all_events:
            by_cat[e.category.value] += 1
            if e.device_id:
                by_dev[e.device_id] += 1

        timestamps = [e.timestamp for e in all_events]
        return EventSummary(
            total_events=len(all_events),
            by_category=dict(by_cat),
            by_device=dict(by_dev),
            earliest=min(timestamps) if timestamps else None,
            latest=max(timestamps) if timestamps else None,
        )
