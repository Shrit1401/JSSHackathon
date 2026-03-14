from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional

from ..models import (
    DeviceType, DeviceFeatureVector, Confidence,
    RiskLevel, SignalBreakdown, DeviceTrustScore, DeviceTrustHistory, TrustSummary,
)
from .drift import DriftDetector
from .policy import PolicyEngine
from .ml import MLDetector
from .baseline import BaselineEngine
from .protection import BaselineProtector

W_ML = 40.0
W_DRIFT = 20.0
W_DRIFT_CONFIRMED = 15.0
W_POLICY_PER_HIGH = 10.0
W_POLICY_CAP = 30.0
BASELINE_UPDATE_THRESHOLD = 85.0
DRIFT_NORMALIZE_CAP = 100.0


def _classify_risk(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.SAFE
    if score >= 60:
        return RiskLevel.LOW
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


class TrustEngine:
    def __init__(self, drift_detector: DriftDetector, policy_engine: PolicyEngine, ml_detector: MLDetector, baseline_engine: BaselineEngine):
        self.drift_detector = drift_detector
        self.policy_engine = policy_engine
        self.ml_detector = ml_detector
        self.baseline_engine = baseline_engine
        self.protector = BaselineProtector(baseline_engine)
        self.history: dict[str, list[DeviceTrustScore]] = defaultdict(list)
        self._latest_features: dict[str, DeviceFeatureVector] = {}

    def compute_trust(self, device_id: str, device_type: DeviceType) -> DeviceTrustScore:
        ml_score = 0.0
        ml_scores = self.ml_detector.get_device_scores(device_id)
        if ml_scores:
            ml_score = ml_scores[-1].anomaly_score
        ml_penalty = round(ml_score * W_ML, 2)

        drift_raw = 0.0
        drift_confirmed = False
        drift_state = self.drift_detector.get_device_state(device_id)
        if drift_state:
            drift_raw = drift_state.latest_drift_score
            drift_confirmed = drift_state.consecutive_drift_windows >= 3
        drift_normalized = round(min(drift_raw / DRIFT_NORMALIZE_CAP, 1.0), 4)
        drift_penalty = round(drift_normalized * W_DRIFT, 2)
        drift_conf_penalty = W_DRIFT_CONFIRMED if drift_confirmed else 0.0

        policy_state = self.policy_engine.get_device_state(device_id)
        total_violations = 0
        high_conf_count = 0
        if policy_state:
            total_violations = policy_state.total_violations
            device_violations = self.policy_engine.get_violations(device_id=device_id)
            high_conf_count = sum(1 for v in device_violations if v.confidence == Confidence.HIGH)
        policy_penalty = round(min(high_conf_count * W_POLICY_PER_HIGH, W_POLICY_CAP), 2)

        total_penalty = ml_penalty + drift_penalty + drift_conf_penalty + policy_penalty
        trust = round(max(0.0, min(100.0, 100.0 - total_penalty)), 2)
        risk = _classify_risk(trust)

        breakdown = SignalBreakdown(
            ml_anomaly_score=round(ml_score, 4), ml_penalty=ml_penalty,
            drift_score=round(drift_raw, 4), drift_normalized=drift_normalized,
            drift_penalty=drift_penalty, drift_confirmed=drift_confirmed,
            drift_confirmation_penalty=drift_conf_penalty,
            policy_violations_total=total_violations,
            policy_high_confidence=high_conf_count, policy_penalty=policy_penalty,
            total_penalty=round(total_penalty, 2),
        )

        latest_fv = self._latest_features.get(device_id)
        gate_decision = self.protector.gate_check(device_id, device_type, trust, latest_fv)
        baseline_allowed = gate_decision.value == "allowed"

        result = DeviceTrustScore(
            device_id=device_id, device_type=device_type, trust_score=trust,
            risk_level=risk, signal_breakdown=breakdown,
            baseline_update_allowed=baseline_allowed, timestamp=datetime.now(timezone.utc),
        )
        self.history[device_id].append(result)

        if baseline_allowed and latest_fv:
            self.baseline_engine.update_device_baseline(device_id, latest_fv)
        return result

    def ingest_features(self, features: list[DeviceFeatureVector]):
        for fv in features:
            self._latest_features[fv.device_id] = fv

    def compute_all(self, devices: list[tuple[str, DeviceType]]) -> list[DeviceTrustScore]:
        return [self.compute_trust(did, dtype) for did, dtype in devices]

    def get_device_trust(self, device_id: str) -> Optional[DeviceTrustScore]:
        if device_id in self.history and self.history[device_id]:
            return self.history[device_id][-1]
        return None

    def get_all_latest(self) -> list[DeviceTrustScore]:
        results = []
        for scores in self.history.values():
            if scores:
                results.append(scores[-1])
        return sorted(results, key=lambda s: s.trust_score)

    def get_device_history(self, device_id: str) -> Optional[DeviceTrustHistory]:
        scores = self.history.get(device_id, [])
        if not scores:
            return None
        trust_vals = [s.trust_score for s in scores]
        return DeviceTrustHistory(
            device_id=device_id, device_type=scores[0].device_type,
            scores=scores, current_score=trust_vals[-1],
            current_risk=scores[-1].risk_level,
            lowest_score=min(trust_vals), highest_score=max(trust_vals),
            average_score=round(sum(trust_vals) / len(trust_vals), 2),
        )

    def get_summary(self) -> TrustSummary:
        latest = self.get_all_latest()
        by_risk = defaultdict(int)
        for s in latest:
            by_risk[s.risk_level.value] += 1
        trust_vals = [s.trust_score for s in latest]
        avg = round(sum(trust_vals) / max(len(trust_vals), 1), 2)
        lowest_dev = None
        lowest_score = 100.0
        for s in latest:
            if s.trust_score < lowest_score:
                lowest_score = s.trust_score
                lowest_dev = s.device_id
        blocked = sum(1 for s in latest if not s.baseline_update_allowed)

        return TrustSummary(
            total_devices=len(latest), devices_by_risk=dict(by_risk),
            average_trust=avg, lowest_trust_device=lowest_dev,
            lowest_trust_score=lowest_score, baseline_updates_blocked=blocked,
            weights={"ml_anomaly": W_ML, "drift": W_DRIFT, "drift_confirmed_bonus": W_DRIFT_CONFIRMED, "policy_per_high_conf": W_POLICY_PER_HIGH, "policy_cap": W_POLICY_CAP},
        )
