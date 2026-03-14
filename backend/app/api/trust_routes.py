from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.trust import RiskLevel, DeviceTrustScore, DeviceTrustHistory, TrustSummary
from app.models.protection import (
    GateDecision,
    DeviceProtectionState,
    GateEvent,
    PoisoningAttempt,
    ProtectionSummary,
)
from app.services.trust_engine import TrustEngine
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.baseline_routes import baseline_engine

router = APIRouter(prefix="/trust", tags=["Trust Scoring"])

trust_engine = TrustEngine(drift_detector, policy_engine, ml_detector, baseline_engine)

_all_features = feature_engine.process_all_windows(generator.get_all_telemetry())
trust_engine.ingest_features(_all_features)
_devices = [(d.device_id, d.device_type) for d in generator.devices]
trust_engine.compute_all(_devices)


@router.get("/scores")
def get_all_trust_scores(
    device_type: Optional[DeviceType] = None,
    risk_level: Optional[RiskLevel] = None,
) -> list[DeviceTrustScore]:
    scores = trust_engine.get_all_latest()
    if device_type:
        scores = [s for s in scores if s.device_type == device_type]
    if risk_level:
        scores = [s for s in scores if s.risk_level == risk_level]
    return scores


@router.get("/scores/{device_id}")
def get_device_trust(device_id: str) -> DeviceTrustScore:
    score = trust_engine.get_device_trust(device_id)
    if not score:
        raise HTTPException(status_code=404, detail=f"No trust score for '{device_id}'")
    return score


@router.get("/scores/{device_id}/history")
def get_device_trust_history(device_id: str) -> DeviceTrustHistory:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    history = trust_engine.get_device_history(device_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No trust history for '{device_id}'")
    return history


@router.get("/at-risk")
def get_at_risk_devices() -> list[DeviceTrustScore]:
    high = trust_engine.get_devices_by_risk(RiskLevel.HIGH)
    medium = trust_engine.get_devices_by_risk(RiskLevel.MEDIUM)
    return high + medium


@router.post("/recompute")
def recompute_all_trust() -> list[DeviceTrustScore]:
    latest_features = feature_engine.get_latest_features()
    if latest_features:
        trust_engine.ingest_features(latest_features)
    devices = [(d.device_id, d.device_type) for d in generator.devices]
    return trust_engine.compute_all(devices)


@router.get("/summary")
def get_trust_summary() -> TrustSummary:
    return trust_engine.get_summary()


@router.get("/protection/status")
def get_all_protection_states() -> list[DeviceProtectionState]:
    return trust_engine.protector.get_all_device_states()


@router.get("/protection/status/{device_id}")
def get_device_protection(device_id: str) -> DeviceProtectionState:
    state = trust_engine.protector.get_device_state(device_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No protection state for '{device_id}'")
    return state


@router.get("/protection/quarantined")
def get_quarantined_devices() -> list[DeviceProtectionState]:
    return trust_engine.protector.get_quarantined_devices()


@router.post("/protection/lift-quarantine/{device_id}")
def lift_quarantine(device_id: str):
    if not trust_engine.protector.lift_quarantine(device_id):
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' is not quarantined")
    return {"device_id": device_id, "quarantine_lifted": True, "status": "manual_review_accepted"}


@router.get("/protection/gate-log")
def get_gate_log(
    device_id: Optional[str] = None,
    decision: Optional[GateDecision] = None,
    limit: int = Query(default=100, le=500),
) -> list[GateEvent]:
    return trust_engine.protector.get_gate_events(device_id, decision)[-limit:]


@router.get("/protection/poisoning-attempts")
def get_poisoning_attempts(
    device_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
) -> list[PoisoningAttempt]:
    return trust_engine.protector.get_poisoning_attempts(device_id)[-limit:]


@router.get("/protection/summary")
def get_protection_summary() -> ProtectionSummary:
    return trust_engine.protector.get_summary()
