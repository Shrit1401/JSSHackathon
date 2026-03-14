from typing import Optional

from app.models.telemetry import DeviceType
from app.services.drift_detector import DriftDetector
from app.services.policy_engine import PolicyEngine
from app.services.ml_detector import MLDetector
from app.services.trust_engine import TrustEngine
from app.services.baseline_engine import BaselineEngine, NUMERIC_FEATURES


class DeviceExplainer:
    def __init__(
        self,
        drift_detector: DriftDetector,
        policy_engine: PolicyEngine,
        ml_detector: MLDetector,
        trust_engine: TrustEngine,
        baseline_engine: BaselineEngine,
    ):
        self.drift = drift_detector
        self.policy = policy_engine
        self.ml = ml_detector
        self.trust = trust_engine
        self.baseline = baseline_engine

    def explain(self, device_id: str, device_type: DeviceType) -> dict:
        reasons = []
        signals = {}
        recommendations = []

        trust_score = self._explain_trust(device_id, reasons, signals)
        self._explain_ml(device_id, reasons, signals)
        self._explain_drift(device_id, reasons, signals)
        self._explain_policy(device_id, device_type, reasons, signals)
        self._explain_protection(device_id, reasons, signals)
        self._explain_baseline_comparison(device_id, reasons, signals)
        self._generate_recommendations(device_id, signals, recommendations)

        is_flagged = trust_score is not None and trust_score < 80

        return {
            "device_id": device_id,
            "device_type": device_type.value,
            "is_flagged": is_flagged,
            "trust_score": trust_score,
            "risk_level": signals.get("risk_level", "UNKNOWN"),
            "reasons": reasons,
            "signal_details": signals,
            "recommendations": recommendations,
            "summary": self._build_summary(device_id, reasons, is_flagged),
        }

    def _explain_trust(self, device_id: str, reasons: list, signals: dict) -> Optional[float]:
        ts = self.trust.get_device_trust(device_id)
        if not ts:
            return None

        signals["trust_score"] = ts.trust_score
        signals["risk_level"] = ts.risk_level.value

        b = ts.signal_breakdown
        signals["penalty_breakdown"] = {
            "ml_penalty": b.ml_penalty,
            "drift_penalty": b.drift_penalty,
            "drift_confirmation_penalty": b.drift_confirmation_penalty,
            "policy_penalty": b.policy_penalty,
            "total_penalty": b.total_penalty,
        }

        if b.ml_penalty > 15:
            reasons.append(f"ML model detected anomalous behavior (penalty: -{b.ml_penalty:.0f})")
        if b.drift_penalty > 5:
            reasons.append(f"Behavioral drift from baseline (penalty: -{b.drift_penalty:.0f})")
        if b.drift_confirmed:
            reasons.append(f"Drift persisted across 3+ consecutive windows (confirmed drift penalty: -{b.drift_confirmation_penalty:.0f})")
        if b.policy_penalty > 0:
            reasons.append(f"Policy violations detected ({b.policy_high_confidence} high-confidence, penalty: -{b.policy_penalty:.0f})")

        return ts.trust_score

    def _explain_ml(self, device_id: str, reasons: list, signals: dict):
        scores = self.ml.get_device_scores(device_id)
        if not scores:
            return

        latest = scores[-1]
        signals["ml_anomaly_score"] = latest.anomaly_score
        signals["ml_is_anomalous"] = latest.is_anomalous

        if latest.is_anomalous:
            top_features = sorted(latest.feature_contributions.items(), key=lambda x: x[1], reverse=True)[:3]
            feature_explanations = []
            for feat, contrib in top_features:
                pct = contrib * 100
                feature_explanations.append(f"{feat} ({pct:.0f}% contribution)")

            signals["ml_top_contributors"] = dict(top_features)
            reasons.append(
                f"Isolation Forest anomaly score {latest.anomaly_score:.2f} exceeds threshold "
                f"(top features: {', '.join(feature_explanations)})"
            )

    def _explain_drift(self, device_id: str, reasons: list, signals: dict):
        state = self.drift.get_device_state(device_id)
        if not state:
            return

        signals["drift_is_active"] = state.is_drifting
        signals["drift_severity"] = state.current_severity.value
        signals["drift_score"] = state.latest_drift_score
        signals["drift_consecutive_windows"] = state.consecutive_drift_windows
        signals["drift_features"] = state.currently_drifting_features

        if state.is_drifting:
            history = self.drift.get_device_history(device_id)
            latest = history[-1] if history else None

            if latest:
                drifting = [fd for fd in latest.drifting_features if fd.is_drifting]
                drift_details = []
                for fd in sorted(drifting, key=lambda x: x.abs_z_score, reverse=True)[:3]:
                    direction = "above" if fd.z_score > 0 else "below"
                    multiplier = abs(fd.current_value / fd.baseline_mean) if fd.baseline_mean != 0 else 0
                    drift_details.append(
                        f"{fd.feature_name}: {fd.current_value:.1f} vs baseline {fd.baseline_mean:.1f} "
                        f"({multiplier:.1f}x {direction}, z={fd.z_score:+.1f})"
                    )

                signals["drift_feature_details"] = drift_details
                for detail in drift_details:
                    reasons.append(f"Feature deviation: {detail}")

    def _explain_policy(self, device_id: str, device_type: DeviceType, reasons: list, signals: dict):
        violations = self.policy.get_violations(device_id=device_id)
        if not violations:
            signals["policy_violations"] = 0
            return

        signals["policy_violations"] = len(violations)

        seen_rules = set()
        for v in violations:
            if v.rule_id in seen_rules:
                continue
            seen_rules.add(v.rule_id)

            evidence_str = ", ".join(f"{k}={v_}" for k, v_ in v.evidence.items()) if v.evidence else ""
            reasons.append(
                f"Policy {v.rule_id} violated: {v.description}"
                + (f" [evidence: {evidence_str}]" if evidence_str else "")
            )

        signals["policy_violation_rules"] = sorted(seen_rules)

    def _explain_protection(self, device_id: str, reasons: list, signals: dict):
        ps = self.trust.protector.get_device_state(device_id)
        if not ps:
            return

        signals["protection_status"] = ps.status.value
        signals["baseline_integrity"] = ps.baseline_integrity
        signals["poisoning_attempts"] = ps.poisoning_attempts

        if ps.is_quarantined:
            reasons.append(
                f"Device QUARANTINED — baseline denied {ps.consecutive_denied} consecutive times, "
                f"{ps.poisoning_attempts} poisoning attempts detected"
            )
        elif ps.is_frozen:
            reasons.append(
                f"Baseline frozen — trust too low for safe model updates "
                f"(integrity: {ps.baseline_integrity:.0%})"
            )

    def _explain_baseline_comparison(self, device_id: str, reasons: list, signals: dict):
        baseline = self.baseline.get_device_baseline(device_id)
        if not baseline:
            return

        signals["baseline_windows_learned"] = baseline.windows_learned
        signals["baseline_frozen"] = baseline.is_frozen
        signals["allowed_protocols"] = baseline.allowed_protocols

    def _generate_recommendations(self, device_id: str, signals: dict, recommendations: list):
        if signals.get("protection_status") == "quarantined":
            recommendations.append("Isolate device from network for manual inspection")
            recommendations.append("Review all traffic logs for IOC (Indicators of Compromise)")
            recommendations.append("If safe: POST /trust/protection/lift-quarantine/" + device_id)

        if signals.get("drift_is_active"):
            recommendations.append("Investigate drifting features for root cause")
            if signals.get("drift_consecutive_windows", 0) >= 3:
                recommendations.append("Confirmed persistent drift — consider network isolation")

        if signals.get("policy_violations", 0) > 0:
            recommendations.append("Review violated policies and update device ACLs if needed")

        if signals.get("ml_is_anomalous"):
            recommendations.append("Cross-reference ML anomaly with drift and policy signals for confidence")

        if not any([
            signals.get("drift_is_active"),
            signals.get("ml_is_anomalous"),
            signals.get("policy_violations", 0) > 0,
        ]):
            recommendations.append("No active threats detected — continue monitoring")

    def _build_summary(self, device_id: str, reasons: list, is_flagged: bool) -> str:
        if not is_flagged:
            return f"{device_id} is operating within normal parameters. No anomalies detected."

        if not reasons:
            return f"{device_id} has a low trust score but no specific reasons could be identified."

        intro = f"{device_id} is flagged because:"
        bullet_points = "\n".join(f"  - {r}" for r in reasons[:5])
        return f"{intro}\n{bullet_points}"
