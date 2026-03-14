from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.ml import AnomalyScore, MLModelInfo, MLSummary
from app.services.ml_detector import MLDetector
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine

router = APIRouter(prefix="/ml", tags=["ML Anomaly Detection"])

ml_detector = MLDetector()

_baseline_features = feature_engine.process_all_windows(generator.get_all_telemetry())
ml_detector.train_on_baseline(_baseline_features)
ml_detector.score_batch(_baseline_features)


@router.get("/scores/latest")
def get_latest_scores(device_type: Optional[DeviceType] = None) -> list[AnomalyScore]:
    scores = ml_detector.get_latest_scores()
    if device_type:
        scores = [s for s in scores if s.device_type == device_type]
    return scores


@router.get("/scores/{device_id}")
def get_device_scores(device_id: str, limit: int = Query(default=50, le=200)) -> list[AnomalyScore]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return ml_detector.get_device_scores(device_id)[-limit:]


@router.get("/scores/{device_id}/latest")
def get_device_latest_score(device_id: str) -> AnomalyScore:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    scores = ml_detector.get_device_scores(device_id)
    if not scores:
        raise HTTPException(status_code=404, detail=f"No ML scores for '{device_id}'")
    return scores[-1]


@router.get("/anomalous")
def get_anomalous_devices() -> list[AnomalyScore]:
    return ml_detector.get_anomalous_devices()


@router.post("/score-latest")
def score_latest_window() -> list[AnomalyScore]:
    latest_features = feature_engine.get_latest_features()
    if not latest_features:
        raise HTTPException(status_code=400, detail="No features to score")
    return ml_detector.score_batch(latest_features)


@router.get("/model")
def get_model_info() -> MLModelInfo:
    info = ml_detector.get_model_info()
    if not info:
        raise HTTPException(status_code=404, detail="No model loaded")
    return info


@router.get("/summary")
def get_ml_summary() -> MLSummary:
    return ml_detector.get_summary()
