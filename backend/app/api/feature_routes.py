from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.features import DeviceFeatureVector, DeviceFeatureTimeline, FeatureSummary
from app.services.feature_engine import FeatureEngine
from app.api.telemetry_routes import generator

router = APIRouter(prefix="/features", tags=["Feature Engineering"])

engine = FeatureEngine()
engine.process_all_windows(generator.get_all_telemetry())


@router.get("/latest")
def get_latest_features(device_type: Optional[DeviceType] = None) -> list[DeviceFeatureVector]:
    features = engine.get_latest_features()
    if device_type:
        features = [f for f in features if f.device_type == device_type]
    return features


@router.get("/window/{window_id}")
def get_window_features(window_id: int) -> list[DeviceFeatureVector]:
    features = engine.get_window_features(window_id)
    if not features:
        raise HTTPException(status_code=404, detail=f"No features for window {window_id}")
    return features


@router.get("/device/{device_id}")
def get_device_features(device_id: str) -> list[DeviceFeatureVector]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    features = engine.get_device_features(device_id)
    if not features:
        raise HTTPException(status_code=404, detail=f"No features computed for '{device_id}'")
    return features


@router.get("/device/{device_id}/timeline")
def get_device_timeline(device_id: str) -> DeviceFeatureTimeline:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    timeline = engine.get_device_timeline(device_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"No feature timeline for '{device_id}'")
    return timeline


@router.get("/summary")
def get_feature_summary() -> FeatureSummary:
    return engine.get_summary()


@router.post("/recompute")
def recompute_features():
    engine.reset()
    all_records = generator.get_all_telemetry()
    features = engine.process_all_windows(all_records)
    return {
        "status": "recomputed",
        "features_generated": len(features),
        "summary": engine.get_summary(),
    }
