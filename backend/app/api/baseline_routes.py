from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.baseline import DeviceBaseline, DeviceTypeBaseline, BaselineDeviation, BaselineSummary
from app.services.baseline_engine import BaselineEngine
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine

router = APIRouter(prefix="/baselines", tags=["Baseline Learning"])

baseline_engine = BaselineEngine()
baseline_engine.learn_all_baselines(feature_engine.process_all_windows(generator.get_all_telemetry()))


@router.get("/devices")
def get_all_device_baselines(device_type: Optional[DeviceType] = None) -> list[DeviceBaseline]:
    baselines = baseline_engine.get_all_device_baselines()
    if device_type:
        baselines = [b for b in baselines if b.device_type == device_type]
    return baselines


@router.get("/devices/{device_id}")
def get_device_baseline(device_id: str) -> DeviceBaseline:
    baseline = baseline_engine.get_device_baseline(device_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"No baseline for device '{device_id}'")
    return baseline


@router.get("/types")
def get_all_type_baselines() -> list[DeviceTypeBaseline]:
    return baseline_engine.get_all_type_baselines()


@router.get("/types/{device_type}")
def get_type_baseline(device_type: DeviceType) -> DeviceTypeBaseline:
    baseline = baseline_engine.get_type_baseline(device_type)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"No baseline for type '{device_type.value}'")
    return baseline


@router.get("/deviation/{device_id}")
def get_device_deviation(
    device_id: str,
    threshold: float = Query(default=2.5, ge=0.5, le=10.0),
) -> list[BaselineDeviation]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    features = feature_engine.get_device_features(device_id)
    if not features:
        raise HTTPException(status_code=404, detail=f"No features for '{device_id}'")

    return [baseline_engine.compute_deviation(fv, threshold) for fv in features]


@router.get("/deviation/{device_id}/latest")
def get_latest_deviation(
    device_id: str,
    threshold: float = Query(default=2.5, ge=0.5, le=10.0),
) -> BaselineDeviation:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    features = feature_engine.get_device_features(device_id)
    if not features:
        raise HTTPException(status_code=404, detail=f"No features for '{device_id}'")

    return baseline_engine.compute_deviation(features[-1], threshold)


@router.post("/freeze/{device_id}")
def freeze_baseline(device_id: str):
    if not baseline_engine.freeze_device(device_id):
        raise HTTPException(status_code=404, detail=f"No baseline for device '{device_id}'")
    return {"device_id": device_id, "is_frozen": True}


@router.post("/unfreeze/{device_id}")
def unfreeze_baseline(device_id: str):
    if not baseline_engine.unfreeze_device(device_id):
        raise HTTPException(status_code=404, detail=f"No baseline for device '{device_id}'")
    return {"device_id": device_id, "is_frozen": False}


@router.post("/relearn")
def relearn_baselines():
    baseline_engine.reset()
    all_features = feature_engine.process_all_windows(generator.get_all_telemetry())
    result = baseline_engine.learn_all_baselines(all_features)
    return {"status": "relearned", **result}


@router.get("/summary")
def get_baseline_summary() -> BaselineSummary:
    return baseline_engine.get_summary()
