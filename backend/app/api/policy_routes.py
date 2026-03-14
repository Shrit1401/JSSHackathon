from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.policy import PolicyType, Confidence, PolicyRule, PolicyViolation, DevicePolicyState, PolicySummary
from app.services.policy_engine import PolicyEngine
from app.api.telemetry_routes import generator

router = APIRouter(prefix="/policies", tags=["Policy Engine"])

policy_engine = PolicyEngine()
policy_engine.evaluate_records(generator.get_all_telemetry())


@router.get("/rules")
def get_rules(device_type: Optional[DeviceType] = None) -> list[PolicyRule]:
    return policy_engine.get_rules(device_type)


@router.get("/violations")
def get_violations(
    device_id: Optional[str] = None,
    policy_type: Optional[PolicyType] = None,
    confidence: Optional[Confidence] = None,
    limit: int = Query(default=50, le=500),
) -> list[PolicyViolation]:
    return policy_engine.get_violations(device_id, policy_type, confidence)[-limit:]


@router.get("/violations/high-confidence")
def get_high_confidence_violations(limit: int = Query(default=50, le=500)) -> list[PolicyViolation]:
    return policy_engine.get_violations(confidence=Confidence.HIGH)[-limit:]


@router.get("/devices")
def get_all_device_policy_states(device_type: Optional[DeviceType] = None) -> list[DevicePolicyState]:
    states = policy_engine.get_all_device_states()
    if device_type:
        states = [s for s in states if s.device_type == device_type]
    return states


@router.get("/devices/{device_id}")
def get_device_policy_state(device_id: str) -> DevicePolicyState:
    state = policy_engine.get_device_state(device_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No policy state for '{device_id}'")
    return state


@router.get("/devices/{device_id}/violations")
def get_device_violations(device_id: str, limit: int = Query(default=50, le=500)) -> list[PolicyViolation]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return policy_engine.get_violations(device_id=device_id)[-limit:]


@router.get("/non-compliant")
def get_non_compliant_devices() -> list[DevicePolicyState]:
    return policy_engine.get_non_compliant_devices()


@router.post("/evaluate-latest")
def evaluate_latest_window():
    latest = generator.get_latest_window()
    if not latest:
        raise HTTPException(status_code=400, detail="No telemetry to evaluate")
    results = policy_engine.evaluate_records(latest)
    violations = [r for r in results if not r.is_compliant]
    return {
        "records_evaluated": len(results),
        "records_with_violations": len(violations),
        "new_violations": sum(r.violations_found for r in results),
    }


@router.post("/recheck")
def recheck_all():
    policy_engine.reset()
    results = policy_engine.evaluate_records(generator.get_all_telemetry())
    violations = [r for r in results if not r.is_compliant]
    return {
        "records_evaluated": len(results),
        "records_with_violations": len(violations),
        "total_violations": policy_engine.get_summary().total_violations,
    }


@router.get("/summary")
def get_policy_summary() -> PolicySummary:
    return policy_engine.get_summary()
