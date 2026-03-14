import logging
from datetime import datetime, timezone
from typing import Optional

from app.calculate.models import DeviceType, AlertSeverity
from app.calculate.engines.telemetry import TelemetryGenerator
from app.calculate.engines.features import FeatureEngine
from app.calculate.engines.baseline import BaselineEngine
from app.calculate.engines.drift import DriftDetector
from app.calculate.engines.policy import PolicyEngine
from app.calculate.engines.ml import MLDetector
from app.calculate.engines.trust import TrustEngine
from app.calculate.engines.alerts import AlertManager
from app.calculate.device_profiles import ATTACK_PROFILES

logger = logging.getLogger("iot_monitor.ml_pipeline")

SUPABASE_TO_INTERNAL_TYPE: dict[str, DeviceType] = {
    "gateway": DeviceType.NETWORK_GATEWAY,
    "camera": DeviceType.CAMERA,
    "sensor": DeviceType.TEMPERATURE_SENSOR,
    "smart_tv": DeviceType.SMART_TV,
    "laptop": DeviceType.LAPTOP,
    "printer": DeviceType.PRINTER,
    "thermostat": DeviceType.THERMOSTAT,
    "hub": DeviceType.SMART_LIGHT_HUB,
    "smartphone": DeviceType.LAPTOP,
    "router": DeviceType.ROUTER,
    "smart_door_lock": DeviceType.SMART_DOOR_LOCK,
    "temperature_sensor": DeviceType.TEMPERATURE_SENSOR,
    "smart_light_hub": DeviceType.SMART_LIGHT_HUB,
    "network_gateway": DeviceType.NETWORK_GATEWAY,
}

API_TO_PIPELINE_ATTACK: dict[str, str] = {
    "TRAFFIC_SPIKE": "traffic_spike",
    "POLICY_VIOLATION": "protocol_misuse",
    "NEW_DESTINATION": "lateral_movement",
    "BACKDOOR": "backdoor",
    "DATA_EXFILTRATION": "data_exfiltration",
    "BOTNET": "botnet",
    "LATERAL_MOVEMENT": "lateral_movement",
    "PROTOCOL_MISUSE": "protocol_misuse",
    "backdoor": "backdoor",
    "data_exfiltration": "data_exfiltration",
    "traffic_spike": "traffic_spike",
    "protocol_misuse": "protocol_misuse",
    "botnet": "botnet",
    "lateral_movement": "lateral_movement",
}

SEVERITY_RANK = {
    "CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0,
}


class MLPipeline:
    def __init__(self):
        self.generator = TelemetryGenerator(seed=42)
        self.feature_engine = FeatureEngine()
        self.baseline_engine = BaselineEngine()
        self.drift_detector = DriftDetector(self.baseline_engine)
        self.policy_engine = PolicyEngine()
        self.ml_detector = MLDetector()
        self.trust_engine = TrustEngine(
            self.drift_detector, self.policy_engine,
            self.ml_detector, self.baseline_engine,
        )
        self.alert_manager = AlertManager(
            self.drift_detector, self.policy_engine,
            self.ml_detector, self.trust_engine,
        )

        self.is_trained = False
        self.device_map: dict[str, str] = {}
        self.reverse_map: dict[str, str] = {}
        self.active_attacks: dict[str, str] = {}
        self._all_devices: list[tuple[str, DeviceType]] = []
        self._last_alert_count = 0

    def initialize(self, supabase_devices: list[dict]) -> None:
        self._map_devices(supabase_devices)

        logger.info("ML pipeline: generating baseline telemetry (5 windows)...")
        baseline_records = self.generator.generate_baseline_windows(
            num_windows=5, records_per_device=3,
        )
        baseline_features = self.feature_engine.process_all_windows(baseline_records)
        self.baseline_engine.learn_all_baselines(baseline_features)

        logger.info("ML pipeline: training Isolation Forest on %d feature vectors...", len(baseline_features))
        self.ml_detector.train_on_baseline(baseline_features)

        clean_records = self.generator.generate_window(records_per_device=3)
        clean_features = self.feature_engine.process_window(clean_records)
        self.drift_detector.analyze_window(clean_features)
        self.policy_engine.evaluate_records(clean_records)
        self.ml_detector.score_batch(clean_features)
        self.trust_engine.ingest_features(clean_features)
        self.trust_engine.compute_all(self._all_devices)

        self.is_trained = True
        logger.info("ML pipeline initialized — %d devices mapped, model trained.", len(self.device_map))

    def _map_devices(self, supabase_devices: list[dict]) -> None:
        self._all_devices = [(d.device_id, d.device_type) for d in self.generator.devices]

        used_internal: set[str] = set()
        for sd in supabase_devices:
            dtype = SUPABASE_TO_INTERNAL_TYPE.get(sd["device_type"])
            if not dtype:
                logger.warning("No internal type mapping for supabase device_type=%s", sd["device_type"])
                continue
            for device in self.generator.devices:
                if device.device_type == dtype and device.device_id not in used_internal:
                    self.device_map[sd["id"]] = device.device_id
                    self.reverse_map[device.device_id] = sd["id"]
                    used_internal.add(device.device_id)
                    break

    def run_tick(self) -> dict[str, dict]:
        if not self.is_trained:
            return {}

        attack_devices = dict(self.active_attacks)
        records = self.generator.generate_window(
            records_per_device=3, attack_devices=attack_devices,
        )
        features = self.feature_engine.process_window(records)
        self.drift_detector.analyze_window(features)
        self.policy_engine.evaluate_records(records)
        self.ml_detector.score_batch(features)
        self.trust_engine.ingest_features(features)
        trust_scores = self.trust_engine.compute_all(self._all_devices)

        results = {}
        for ts in trust_scores:
            supa_id = self.reverse_map.get(ts.device_id)
            if supa_id:
                risk_str = ts.risk_level.value
                if risk_str == "HIGH":
                    risk_str = "COMPROMISED"
                results[supa_id] = {
                    "trust_score": int(round(ts.trust_score)),
                    "risk_level": risk_str,
                    "signal_breakdown": ts.signal_breakdown.model_dump(),
                    "baseline_update_allowed": ts.baseline_update_allowed,
                }
        return results

    def start_attack(self, supabase_device_id: str, attack_type: str) -> Optional[str]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        pipeline_attack = API_TO_PIPELINE_ATTACK.get(attack_type, "backdoor")
        self.active_attacks[internal_id] = pipeline_attack
        logger.info("Attack started: %s on %s (internal=%s)", pipeline_attack, supabase_device_id, internal_id)
        return pipeline_attack

    def stop_attack(self, supabase_device_id: str) -> None:
        internal_id = self.device_map.get(supabase_device_id)
        if internal_id:
            self.active_attacks.pop(internal_id, None)

    def stop_all_attacks(self) -> None:
        self.active_attacks.clear()

    def run_attack_cycles(self, supabase_device_id: str, attack_type: str, cycles: int = 3) -> dict:
        self.start_attack(supabase_device_id, attack_type)
        result = {}
        for _ in range(cycles):
            tick_results = self.run_tick()
            if supabase_device_id in tick_results:
                result = tick_results[supabase_device_id]
        return result

    def get_new_alerts(self) -> list[dict]:
        self.alert_manager.scan_all()
        all_alerts = self.alert_manager.alerts
        new_alerts = all_alerts[self._last_alert_count:]
        self._last_alert_count = len(all_alerts)

        result = []
        for a in new_alerts:
            supa_id = self.reverse_map.get(a.device_id, a.device_id)
            sev = a.severity.value
            result.append({
                "device_id": supa_id,
                "alert_type": a.alert_type.value,
                "severity": sev,
                "message": f"[ML] {a.title}: {a.reason}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return sorted(result, key=lambda x: SEVERITY_RANK.get(x["severity"], 0), reverse=True)

    def get_device_trust_detail(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        ts = self.trust_engine.get_device_trust(internal_id)
        if not ts:
            return None
        breakdown = ts.signal_breakdown
        return {
            "trust_score": round(ts.trust_score, 2),
            "risk_level": ts.risk_level.value,
            "ml_anomaly_score": round(breakdown.ml_anomaly_score, 4),
            "ml_penalty": round(breakdown.ml_penalty, 2),
            "drift_score": round(breakdown.drift_score, 4),
            "drift_penalty": round(breakdown.drift_penalty, 2),
            "drift_confirmed": breakdown.drift_confirmed,
            "drift_confirmation_penalty": round(breakdown.drift_confirmation_penalty, 2),
            "policy_violations_total": breakdown.policy_violations_total,
            "policy_high_confidence": breakdown.policy_high_confidence,
            "policy_penalty": round(breakdown.policy_penalty, 2),
            "total_penalty": round(breakdown.total_penalty, 2),
            "baseline_update_allowed": ts.baseline_update_allowed,
        }

    def get_device_features(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        fv = self.trust_engine._latest_features.get(internal_id)
        if not fv:
            return None
        return {
            "packet_rate": round(fv.packet_rate, 2),
            "avg_session_duration": round(fv.avg_session_duration, 2),
            "total_bytes_sent": fv.total_bytes_sent,
            "total_bytes_received": fv.total_bytes_received,
            "traffic_volume": fv.traffic_volume,
            "unique_destinations": fv.unique_destinations,
            "destination_entropy": round(fv.destination_entropy, 4),
            "unique_protocols": fv.unique_protocols,
            "protocol_entropy": round(fv.protocol_entropy, 4),
            "protocol_distribution": fv.protocol_distribution,
            "external_connection_ratio": round(fv.external_connection_ratio, 4),
            "inbound_outbound_ratio": round(fv.inbound_outbound_ratio, 4),
            "record_count": fv.record_count,
            "window_start": fv.window_start.isoformat() if fv.window_start else None,
            "window_end": fv.window_end.isoformat() if fv.window_end else None,
        }

    def get_device_baseline(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        bl = self.baseline_engine.get_device_baseline(internal_id)
        if not bl:
            return None
        from app.calculate.engines.baseline import NUMERIC_FEATURES
        stats = {}
        for feat in NUMERIC_FEATURES:
            s = getattr(bl, feat)
            stats[feat] = {
                "mean": round(s.mean, 4),
                "std": round(s.std, 4),
                "min": round(s.min_val, 4),
                "max": round(s.max_val, 4),
                "samples": s.samples,
            }
        return {
            "windows_learned": bl.windows_learned,
            "is_frozen": bl.is_frozen,
            "last_updated": bl.last_updated.isoformat() if bl.last_updated else None,
            "allowed_protocols": bl.allowed_protocols,
            "expected_destination_types": bl.expected_destination_types,
            "feature_stats": stats,
        }

    def get_device_drift(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        state = self.drift_detector.get_device_state(internal_id)
        if not state:
            return None
        history = self.drift_detector.results_history.get(internal_id, [])
        latest = history[-1] if history else None
        drifting_features_detail = []
        if latest:
            for fd in latest.drifting_features:
                if fd.is_drifting:
                    drifting_features_detail.append({
                        "feature": fd.feature_name,
                        "z_score": round(fd.z_score, 4),
                        "baseline_mean": round(fd.baseline_mean, 4),
                        "baseline_std": round(fd.baseline_std, 4),
                        "current_value": round(fd.current_value, 4),
                        "consecutive_windows": fd.consecutive_windows,
                    })
        return {
            "is_drifting": state.is_drifting,
            "severity": state.current_severity.value,
            "drift_score": round(state.latest_drift_score, 4),
            "peak_drift_score": round(state.peak_drift_score, 4),
            "consecutive_drift_windows": state.consecutive_drift_windows,
            "max_consecutive_drift": state.max_consecutive_drift,
            "total_drift_windows": state.total_drift_windows,
            "total_windows_analyzed": state.total_windows_analyzed,
            "currently_drifting_features": state.currently_drifting_features,
            "historically_drifted_features": state.historically_drifted_features,
            "drifting_features_detail": drifting_features_detail,
            "first_drift_detected": state.first_drift_detected.isoformat() if state.first_drift_detected else None,
            "last_drift_detected": state.last_drift_detected.isoformat() if state.last_drift_detected else None,
            "drift_confirmed_at": state.drift_confirmed_at.isoformat() if state.drift_confirmed_at else None,
        }

    def get_device_policy(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        state = self.policy_engine.get_device_state(internal_id)
        if not state:
            return None
        violations = self.policy_engine.get_violations(device_id=internal_id)
        recent = violations[-10:] if len(violations) > 10 else violations
        violation_list = []
        for v in recent:
            violation_list.append({
                "rule_id": v.rule_id,
                "policy_type": v.policy_type.value,
                "confidence": v.confidence.value,
                "description": v.description,
                "evidence": v.evidence,
                "timestamp": v.timestamp.isoformat(),
            })
        return {
            "is_compliant": state.is_compliant,
            "total_records_evaluated": state.total_records_evaluated,
            "total_violations": state.total_violations,
            "violation_rate": round(state.violation_rate, 4),
            "violations_by_type": state.violations_by_type,
            "last_violation": state.last_violation.isoformat() if state.last_violation else None,
            "recent_violations": violation_list,
        }

    def get_device_ml_detail(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        scores = self.ml_detector.get_device_scores(internal_id)
        if not scores:
            return None
        latest = scores[-1]
        history = [
            {"anomaly_score": round(s.anomaly_score, 4), "is_anomalous": s.is_anomalous}
            for s in scores
        ]
        return {
            "anomaly_score": round(latest.anomaly_score, 4),
            "raw_score": round(latest.raw_score, 4),
            "is_anomalous": latest.is_anomalous,
            "threshold": latest.threshold,
            "feature_contributions": {
                k: round(v, 4) for k, v in latest.feature_contributions.items()
            },
            "top_contributing_feature": max(
                latest.feature_contributions,
                key=latest.feature_contributions.get,
            ) if latest.feature_contributions else None,
            "total_scored": len(scores),
            "anomalous_count": sum(1 for s in scores if s.is_anomalous),
            "score_history": history,
        }

    def get_device_protection(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        state = self.trust_engine.protector.get_device_state(internal_id)
        if not state:
            return None
        return {
            "status": state.status.value,
            "is_frozen": state.is_frozen,
            "is_quarantined": state.is_quarantined,
            "trust_score": round(state.trust_score, 2),
            "consecutive_denied": state.consecutive_denied,
            "total_allowed": state.total_allowed,
            "total_denied": state.total_denied,
            "poisoning_attempts": state.poisoning_attempts,
            "baseline_integrity": round(state.baseline_integrity, 4),
            "last_allowed_update": state.last_allowed_update.isoformat() if state.last_allowed_update else None,
            "last_decision": state.last_decision.value if state.last_decision else None,
            "last_decision_time": state.last_decision_time.isoformat() if state.last_decision_time else None,
        }

    def get_device_trust_history(self, supabase_device_id: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        if not internal_id:
            return None
        hist = self.trust_engine.get_device_history(internal_id)
        if not hist:
            return None
        trajectory = [
            {
                "trust_score": round(s.trust_score, 2),
                "risk_level": s.risk_level.value,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in hist.scores
        ]
        return {
            "current_score": round(hist.current_score, 2),
            "current_risk": hist.current_risk.value,
            "lowest_score": round(hist.lowest_score, 2),
            "highest_score": round(hist.highest_score, 2),
            "average_score": round(hist.average_score, 2),
            "total_windows": len(hist.scores),
            "trajectory": trajectory,
        }

    def get_device_full_analytics(self, supabase_device_id: str) -> Optional[dict]:
        if not self.device_map.get(supabase_device_id):
            return None
        return {
            "trust_detail": self.get_device_trust_detail(supabase_device_id),
            "features": self.get_device_features(supabase_device_id),
            "baseline": self.get_device_baseline(supabase_device_id),
            "drift": self.get_device_drift(supabase_device_id),
            "policy": self.get_device_policy(supabase_device_id),
            "ml_anomaly": self.get_device_ml_detail(supabase_device_id),
            "protection": self.get_device_protection(supabase_device_id),
            "trust_history": self.get_device_trust_history(supabase_device_id),
        }

    def get_ml_model_info(self) -> Optional[dict]:
        info = self.ml_detector.get_model_info()
        if not info:
            return None
        return {
            "model_type": info.model_type,
            "training_samples": info.training_samples,
            "training_features": info.training_features,
            "contamination": info.contamination,
            "trained_at": info.trained_at.isoformat() if info.trained_at else None,
            "dataset_source": info.dataset_source,
            "benign_samples": info.benign_samples,
            "malicious_samples": info.malicious_samples,
            "total_scored": self.ml_detector.total_scored,
            "anomalies_detected": self.ml_detector.anomalies_detected,
            "anomaly_rate": round(
                self.ml_detector.anomalies_detected / max(self.ml_detector.total_scored, 1), 4
            ),
        }

    def get_trust_summary(self) -> dict:
        summary = self.trust_engine.get_summary()
        return {
            "total_devices": summary.total_devices,
            "devices_by_risk": summary.devices_by_risk,
            "average_trust": summary.average_trust,
            "lowest_trust_device": self.reverse_map.get(
                summary.lowest_trust_device or "", summary.lowest_trust_device
            ),
            "lowest_trust_score": summary.lowest_trust_score,
            "baseline_updates_blocked": summary.baseline_updates_blocked,
            "weights": summary.weights,
        }

    def get_protection_summary(self) -> dict:
        ps = self.trust_engine.protector.get_summary()
        return {
            "total_devices": ps.total_devices,
            "devices_learning": ps.devices_learning,
            "devices_frozen": ps.devices_frozen,
            "devices_quarantined": ps.devices_quarantined,
            "total_gate_events": ps.total_gate_events,
            "total_allowed": ps.total_allowed,
            "total_denied": ps.total_denied,
            "total_poisoning_attempts": ps.total_poisoning_attempts,
            "average_integrity": ps.average_integrity,
        }

    def reset(self) -> None:
        self.active_attacks.clear()
        self._last_alert_count = 0
        self.__init__()


pipeline = MLPipeline()
