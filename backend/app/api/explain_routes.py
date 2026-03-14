from fastapi import APIRouter, HTTPException

from app.services.explainer import DeviceExplainer
from app.api.telemetry_routes import generator
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.trust_routes import trust_engine
from app.api.baseline_routes import baseline_engine

router = APIRouter(prefix="/devices", tags=["Explainability"])

explainer = DeviceExplainer(drift_detector, policy_engine, ml_detector, trust_engine, baseline_engine)


@router.get("/{device_id}/explain")
def explain_device(device_id: str):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return explainer.explain(device_id, device.device_type)


@router.get("/{device_id}/explain/summary")
def explain_device_short(device_id: str):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    result = explainer.explain(device_id, device.device_type)
    return {
        "device_id": result["device_id"],
        "is_flagged": result["is_flagged"],
        "trust_score": result["trust_score"],
        "risk_level": result["risk_level"],
        "reasons": result["reasons"],
        "summary": result["summary"],
    }
