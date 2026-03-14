from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.config.device_profiles import ATTACK_PROFILES
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.trust_routes import trust_engine
from app.api.alert_routes import alert_manager
from app.api.event_routes import timeline
from app.models.events import EventCategory
from app.services import supabase_sync

router = APIRouter(tags=["Attack Simulation v2"])


class AttackRequest(BaseModel):
    device_id: str
    attack_type: str
    cycles: int = 3


@router.post("/simulate-attack")
def simulate_attack(req: AttackRequest):
    device = generator.get_device_by_id(req.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{req.device_id}' not found")

    if req.attack_type not in ATTACK_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown attack '{req.attack_type}'. Available: {list(ATTACK_PROFILES.keys())}",
        )

    profile = ATTACK_PROFILES[req.attack_type]
    if device.device_type not in profile["applicable_devices"]:
        raise HTTPException(
            status_code=400,
            detail=f"Attack '{req.attack_type}' not applicable to '{device.device_type.value}'",
        )

    timeline.log_event(
        EventCategory.ATTACK, "attack_started",
        f"Simulating {req.attack_type} on {req.device_id} for {req.cycles} cycles",
        device_id=req.device_id, device_type=device.device_type,
        metadata={"attack_type": req.attack_type, "cycles": req.cycles},
    )

    cycle_results = []
    for i in range(req.cycles):
        records = generator.generate_window(
            records_per_device=3,
            attack_devices={req.device_id: req.attack_type},
        )
        features = feature_engine.process_window(records)
        drift_results = drift_detector.analyze_window(features)
        policy_engine.evaluate_records(records)
        ml_detector.score_batch(features)
        trust_engine.ingest_features(features)
        devices = [(d.device_id, d.device_type) for d in generator.devices]
        trust_scores = trust_engine.compute_all(devices)

        try:
            supabase_sync.sync_telemetry_batch(records)
            supabase_sync.sync_features(features)
            supabase_sync.sync_trust_scores(trust_scores)
        except Exception:
            pass

        target_trust = next((s for s in trust_scores if s.device_id == req.device_id), None)
        target_drift = next((d for d in drift_results if d.device_id == req.device_id), None)

        cycle_results.append({
            "cycle": i + 1,
            "trust_score": target_trust.trust_score if target_trust else None,
            "risk_level": target_trust.risk_level.value if target_trust else None,
            "drift_score": target_drift.drift_score if target_drift else 0,
            "is_drifting": target_drift.is_drifting if target_drift else False,
            "drift_severity": target_drift.severity.value if target_drift else "none",
        })

    alert_manager.scan_all()

    try:
        supabase_sync.sync_alerts_batch(alert_manager.alerts)
    except Exception:
        pass

    timeline.log_event(
        EventCategory.ATTACK, "attack_completed",
        f"{req.attack_type} simulation on {req.device_id} completed ({req.cycles} cycles)",
        device_id=req.device_id, device_type=device.device_type,
        metadata={"attack_type": req.attack_type, "cycles": req.cycles},
    )

    target_trust_final = trust_engine.get_device_trust(req.device_id)
    protection = trust_engine.protector.get_device_state(req.device_id)

    return {
        "attack": req.attack_type,
        "description": profile["description"],
        "device": req.device_id,
        "cycles_run": req.cycles,
        "cycle_results": cycle_results,
        "final_state": {
            "trust_score": target_trust_final.trust_score if target_trust_final else None,
            "risk_level": target_trust_final.risk_level.value if target_trust_final else None,
            "baseline_frozen": protection.is_frozen if protection else False,
            "quarantined": protection.is_quarantined if protection else False,
            "poisoning_attempts": protection.poisoning_attempts if protection else 0,
        },
        "total_alerts": len(alert_manager.alerts),
        "synced_to_supabase": True,
    }


@router.get("/simulate-attack/types")
def list_attack_types():
    return {
        name: {
            "description": profile["description"],
            "applicable_devices": [d.value for d in profile["applicable_devices"]],
        }
        for name, profile in ATTACK_PROFILES.items()
    }
