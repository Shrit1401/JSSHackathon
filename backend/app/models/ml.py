from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.telemetry import DeviceType


class AnomalyScore(BaseModel):
    device_id: str
    device_type: DeviceType
    window_id: int
    anomaly_score: float
    raw_score: float
    is_anomalous: bool
    threshold: float
    feature_contributions: dict[str, float]
    timestamp: datetime


class MLModelInfo(BaseModel):
    model_type: str
    training_samples: int
    training_features: list[str]
    contamination: float
    trained_at: Optional[datetime] = None
    dataset_source: str
    benign_samples: int
    malicious_samples: int


class MLSummary(BaseModel):
    model_loaded: bool
    model_info: Optional[MLModelInfo] = None
    total_scored: int
    anomalies_detected: int
    anomaly_rate: float
