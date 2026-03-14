import logging
from datetime import datetime, timezone
from typing import Optional

from app.calculate.models import DeviceType, AlertSeverity, FeatureStats
from app.calculate.engines.telemetry import TelemetryGenerator
from app.calculate.engines.features import FeatureEngine
from app.calculate.engines.baseline import BaselineEngine
from app.calculate.engines.drift import DriftDetector
from app.calculate.engines.policy import PolicyEngine
from app.calculate.engines.ml import MLDetector
from app.calculate.engines.trust import TrustEngine
from app.calculate.engines.alerts import AlertManager
from app.calculate.device_profiles import ATTACK_PROFILES, DEVICE_PROFILES
from app.calculate.engines.baseline import NUMERIC_FEATURES

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

    def get_device_full_profile(self, supabase_device_id: str, supabase_device_type: str) -> Optional[dict]:
        internal_id = self.device_map.get(supabase_device_id)
        internal_type = SUPABASE_TO_INTERNAL_TYPE.get(supabase_device_type)
        if not internal_type:
            return None

        profile_data = DEVICE_PROFILES.get(internal_type)
        profile_section = None
        if profile_data:
            profile_section = {
                "description": profile_data["description"],
                "normal_protocols": [p.value for p in profile_data["normal_protocols"]],
                "suspicious_protocols": [p.value for p in profile_data["suspicious_protocols"]],
                "expected_bytes_sent": {"min": profile_data["bytes_sent"][0], "max": profile_data["bytes_sent"][1]},
                "expected_bytes_received": {"min": profile_data["bytes_received"][0], "max": profile_data["bytes_received"][1]},
                "expected_session_duration": {"min": profile_data["session_duration"][0], "max": profile_data["session_duration"][1]},
                "expected_packet_count": {"min": profile_data["packet_count"][0], "max": profile_data["packet_count"][1]},
                "protocol_weights": {k.value: v for k, v in profile_data["protocol_weights"].items()},
                "normal_destinations": [d.value for d in profile_data["normal_destinations"]],
                "destination_weights": {k.value: v for k, v in profile_data["destination_weights"].items()},
            }

        baseline_section = None
        if internal_id:
            bl = self.baseline_engine.get_device_baseline(internal_id)
            if bl:
                stats = {}
                for feat in NUMERIC_FEATURES:
                    fs: FeatureStats = getattr(bl, feat)
                    stats[feat] = {
                        "mean": fs.mean, "std": fs.std,
                        "min_val": fs.min_val, "max_val": fs.max_val,
                        "samples": fs.samples,
                    }
                baseline_section = {
                    "windows_learned": bl.windows_learned,
                    "is_frozen": bl.is_frozen,
                    "allowed_protocols": bl.allowed_protocols,
                    "expected_destinations": bl.expected_destination_types,
                    "stats": stats,
                }

        drift_section = None
        if internal_id:
            ds = self.drift_detector.get_device_state(internal_id)
            if ds:
                drift_section = {
                    "is_drifting": ds.is_drifting,
                    "severity": ds.current_severity.value,
                    "drift_score": round(ds.latest_drift_score, 4),
                    "consecutive_drift_windows": ds.consecutive_drift_windows,
                    "peak_drift_score": round(ds.peak_drift_score, 4),
                    "currently_drifting_features": ds.currently_drifting_features,
                    "total_windows_analyzed": ds.total_windows_analyzed,
                    "total_drift_windows": ds.total_drift_windows,
                }

        policy_section = None
        if internal_id:
            ps = self.policy_engine.get_device_state(internal_id)
            if ps:
                policy_section = {
                    "is_compliant": ps.is_compliant,
                    "total_violations": ps.total_violations,
                    "violation_rate": ps.violation_rate,
                    "violations_by_type": ps.violations_by_type,
                    "total_records_evaluated": ps.total_records_evaluated,
                }

        anomaly_section = None
        if internal_id:
            scores = self.ml_detector.get_device_scores(internal_id)
            if scores:
                latest = scores[-1]
                anomaly_section = {
                    "anomaly_score": round(latest.anomaly_score, 4),
                    "is_anomalous": latest.is_anomalous,
                    "raw_score": round(latest.raw_score, 4),
                    "feature_contributions": latest.feature_contributions,
                }

        trust_section = None
        if internal_id:
            ts = self.trust_engine.get_device_trust(internal_id)
            if ts:
                bd = ts.signal_breakdown
                signal_out = {
                    "ml_anomaly_score": round(bd.ml_anomaly_score, 4),
                    "ml_penalty": round(bd.ml_penalty, 2),
                    "drift_score": round(bd.drift_score, 4),
                    "drift_penalty": round(bd.drift_penalty, 2),
                    "drift_confirmed": bd.drift_confirmed,
                    "drift_confirmation_penalty": round(bd.drift_confirmation_penalty, 2),
                    "policy_violations_total": bd.policy_violations_total,
                    "policy_high_confidence": bd.policy_high_confidence,
                    "policy_penalty": round(bd.policy_penalty, 2),
                    "total_penalty": round(bd.total_penalty, 2),
                    "baseline_update_allowed": ts.baseline_update_allowed,
                }
                history_scores = self.trust_engine.history.get(internal_id, [])
                history_out = [
                    {"trust_score": round(h.trust_score, 2), "risk_level": h.risk_level.value}
                    for h in history_scores
                ]
                trust_section = {
                    "current_score": round(ts.trust_score, 2),
                    "risk_level": ts.risk_level.value,
                    "signal_breakdown": signal_out,
                    "baseline_update_allowed": ts.baseline_update_allowed,
                    "history": history_out,
                }

        protection_section = None
        if internal_id:
            prot = self.trust_engine.protector.get_device_state(internal_id)
            if prot:
                protection_section = {
                    "status": prot.status.value,
                    "is_frozen": prot.is_frozen,
                    "is_quarantined": prot.is_quarantined,
                    "consecutive_denied": prot.consecutive_denied,
                    "baseline_integrity": prot.baseline_integrity,
                    "poisoning_attempts": prot.poisoning_attempts,
                    "total_allowed": prot.total_allowed,
                    "total_denied": prot.total_denied,
                }

        applicable_attacks = []
        for attack_name, attack_prof in ATTACK_PROFILES.items():
            if internal_type in attack_prof["applicable_devices"]:
                applicable_attacks.append(attack_name)

        return {
            "profile": profile_section,
            "baseline": baseline_section,
            "drift": drift_section,
            "policy": policy_section,
            "anomaly": anomaly_section,
            "trust": trust_section,
            "protection": protection_section,
            "applicable_attacks": applicable_attacks,
        }

    def reset(self) -> None:
        self.active_attacks.clear()
        self._last_alert_count = 0
        self.__init__()


pipeline = MLPipeline()
