from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.config.device_profiles import ATTACK_PROFILES
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine
from app.api.baseline_routes import baseline_engine
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.trust_routes import trust_engine
from app.api.alert_routes import alert_manager
from app.api.event_routes import timeline
from app.models.events import EventCategory

router = APIRouter(prefix="/simulate", tags=["Attack Simulation"])


@router.get("/attacks")
def list_available_attacks():
    return {
        name: {
            "description": profile["description"],
            "applicable_devices": [d.value for d in profile["applicable_devices"]],
        }
        for name, profile in ATTACK_PROFILES.items()
    }


@router.post("/attack")
def run_full_attack_simulation(
    device_id: str,
    attack_type: str,
    cycles: int = Query(default=1, ge=1, le=10),
):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    if attack_type not in ATTACK_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown attack '{attack_type}'. Available: {list(ATTACK_PROFILES.keys())}",
        )

    profile = ATTACK_PROFILES[attack_type]
    if device.device_type not in profile["applicable_devices"]:
        raise HTTPException(
            status_code=400,
            detail=f"Attack '{attack_type}' not applicable to '{device.device_type.value}'",
        )

    timeline.log_event(
        EventCategory.ATTACK, "attack_started",
        f"Simulating {attack_type} on {device_id} for {cycles} cycles",
        device_id=device_id, device_type=device.device_type,
        metadata={"attack_type": attack_type, "cycles": cycles},
    )

    results = []
    for i in range(cycles):
        records = generator.generate_window(
            records_per_device=3,
            attack_devices={device_id: attack_type},
        )
        features = feature_engine.process_window(records)
        drift_results = drift_detector.analyze_window(features)
        policy_engine.evaluate_records(records)
        ml_detector.score_batch(features)
        trust_engine.ingest_features(features)
        devices = [(d.device_id, d.device_type) for d in generator.devices]
        trust_scores = trust_engine.compute_all(devices)

        target_trust = next((s for s in trust_scores if s.device_id == device_id), None)
        target_drift = next((d for d in drift_results if d.device_id == device_id), None)

        results.append({
            "cycle": i + 1,
            "trust_score": target_trust.trust_score if target_trust else None,
            "risk_level": target_trust.risk_level.value if target_trust else None,
            "drift_score": target_drift.drift_score if target_drift else 0,
            "is_drifting": target_drift.is_drifting if target_drift else False,
            "drift_severity": target_drift.severity.value if target_drift else "none",
        })

    alert_manager.scan_all()

    timeline.log_event(
        EventCategory.ATTACK, "attack_completed",
        f"{attack_type} simulation on {device_id} completed ({cycles} cycles)",
        device_id=device_id, device_type=device.device_type,
        metadata={"attack_type": attack_type, "cycles": cycles},
    )

    target_trust_final = trust_engine.get_device_trust(device_id)
    protection = trust_engine.protector.get_device_state(device_id)

    return {
        "attack": attack_type,
        "description": profile["description"],
        "device": device_id,
        "cycles_run": cycles,
        "cycle_results": results,
        "final_state": {
            "trust_score": target_trust_final.trust_score if target_trust_final else None,
            "risk_level": target_trust_final.risk_level.value if target_trust_final else None,
            "baseline_frozen": protection.is_frozen if protection else False,
            "quarantined": protection.is_quarantined if protection else False,
            "poisoning_attempts": protection.poisoning_attempts if protection else 0,
        },
        "total_alerts": len(alert_manager.alerts),
    }


@router.post("/multi-attack")
def run_multi_device_attack(attacks: dict[str, str], cycles: int = Query(default=3, ge=1, le=10)):
    for device_id, attack_type in attacks.items():
        device = generator.get_device_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
        if attack_type not in ATTACK_PROFILES:
            raise HTTPException(status_code=400, detail=f"Unknown attack '{attack_type}'")

    for device_id, attack_type in attacks.items():
        device = generator.get_device_by_id(device_id)
        timeline.log_event(
            EventCategory.ATTACK, "attack_started",
            f"Multi-attack: {attack_type} on {device_id}",
            device_id=device_id, device_type=device.device_type,
            metadata={"attack_type": attack_type},
        )

    cycle_results = []
    for i in range(cycles):
        records = generator.generate_window(
            records_per_device=3,
            attack_devices=attacks,
        )
        features = feature_engine.process_window(records)
        drift_detector.analyze_window(features)
        policy_engine.evaluate_records(records)
        ml_detector.score_batch(features)
        trust_engine.ingest_features(features)
        devices = [(d.device_id, d.device_type) for d in generator.devices]
        trust_engine.compute_all(devices)
        cycle_results.append({"cycle": i + 1, "records_generated": len(records)})

    alert_manager.scan_all()

    device_states = {}
    for device_id in attacks:
        ts = trust_engine.get_device_trust(device_id)
        ps = trust_engine.protector.get_device_state(device_id)
        device_states[device_id] = {
            "trust_score": ts.trust_score if ts else None,
            "risk_level": ts.risk_level.value if ts else None,
            "quarantined": ps.is_quarantined if ps else False,
        }

    return {
        "attacks": attacks,
        "cycles_run": cycles,
        "device_results": device_states,
        "total_alerts": len(alert_manager.alerts),
    }
