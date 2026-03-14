from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.drift import DriftResult, DeviceDriftState, DriftEvent, DriftSummary
from app.services.drift_detector import DriftDetector
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine
from app.api.baseline_routes import baseline_engine

router = APIRouter(prefix="/drift", tags=["Drift Detection"])

drift_detector = DriftDetector(baseline_engine)

_all_features = feature_engine.process_all_windows(generator.get_all_telemetry())
drift_detector.analyze_window(_all_features)


@router.get("/status")
def get_all_drift_status(device_type: Optional[DeviceType] = None) -> list[DeviceDriftState]:
    states = drift_detector.get_all_device_states()
    if device_type:
        states = [s for s in states if s.device_type == device_type]
    return states


@router.get("/status/{device_id}")
def get_device_drift_status(device_id: str) -> DeviceDriftState:
    state = drift_detector.get_device_state(device_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No drift state for '{device_id}'")
    return state


@router.get("/drifting")
def get_drifting_devices() -> list[DeviceDriftState]:
    return drift_detector.get_drifting_devices()


@router.get("/history/{device_id}")
def get_device_drift_history(device_id: str, limit: int = Query(default=50, le=200)) -> list[DriftResult]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return drift_detector.get_device_history(device_id)[-limit:]


@router.get("/history/{device_id}/latest")
def get_latest_drift_result(device_id: str) -> DriftResult:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    history = drift_detector.get_device_history(device_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No drift history for '{device_id}'")
    return history[-1]


@router.get("/events")
def get_drift_events(
    device_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
) -> list[DriftEvent]:
    return drift_detector.get_events(device_id, event_type)[-limit:]


@router.post("/analyze-latest")
def analyze_latest_window() -> list[DriftResult]:
    latest_features = feature_engine.get_latest_features()
    if not latest_features:
        raise HTTPException(status_code=400, detail="No features to analyze")
    return drift_detector.analyze_window(latest_features)


@router.get("/summary")
def get_drift_summary() -> DriftSummary:
    return drift_detector.get_summary()
