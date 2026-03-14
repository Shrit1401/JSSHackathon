from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ..models import DeviceType, DeviceFeatureVector, AnomalyScore, MLModelInfo

INPUT_FEATURES = [
    "packet_rate", "avg_session_duration", "total_bytes_sent",
    "total_bytes_received", "destination_entropy", "protocol_entropy",
]

ANOMALY_THRESHOLD = 0.5


class MLDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.meta = None
        self.scores_store: dict[str, list[AnomalyScore]] = defaultdict(list)
        self.total_scored = 0
        self.anomalies_detected = 0
        self._baseline_mean_score = 0.0
        self._baseline_std_score = 1.0

    def train_on_baseline(self, baseline_features: list[DeviceFeatureVector]):
        X = self._features_to_matrix(baseline_features)
        np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=200, contamination=0.01,
            max_samples="auto", random_state=42, n_jobs=-1,
        )
        self.model.fit(X_scaled)

        raw_scores = self.model.decision_function(X_scaled)
        self._baseline_mean_score = float(np.mean(raw_scores))
        self._baseline_std_score = max(float(np.std(raw_scores)), 0.001)

        self.meta = {
            "model_type": "IsolationForest",
            "n_estimators": 200,
            "contamination": 0.01,
            "training_samples": len(baseline_features),
            "training_features": INPUT_FEATURES,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "dataset_source": "baseline_telemetry",
            "benign_samples": len(baseline_features),
            "malicious_samples": 0,
        }

    def _features_to_matrix(self, features: list[DeviceFeatureVector]) -> np.ndarray:
        rows = [[getattr(fv, feat) for feat in INPUT_FEATURES] for fv in features]
        return np.array(rows, dtype=np.float64)

    def _raw_to_anomaly_score(self, raw_score: float) -> float:
        z = (self._baseline_mean_score - raw_score) / self._baseline_std_score
        score = 1.0 / (1.0 + np.exp(-z))
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    def _compute_contributions(self, fv: DeviceFeatureVector, scaled: np.ndarray) -> dict[str, float]:
        contributions = {feat: round(abs(float(scaled[0, i])), 4) for i, feat in enumerate(INPUT_FEATURES)}
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: round(v / total, 4) for k, v in contributions.items()}
        return contributions

    def score(self, feature_vector: DeviceFeatureVector) -> AnomalyScore:
        if not self.model or not self.scaler:
            raise RuntimeError("ML model not loaded. Run training first.")

        X = np.array([[getattr(feature_vector, feat) for feat in INPUT_FEATURES]], dtype=np.float64)
        np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        X_scaled = self.scaler.transform(X)
        raw_score = float(self.model.decision_function(X_scaled)[0])
        anomaly_score = self._raw_to_anomaly_score(raw_score)
        is_anomalous = anomaly_score >= ANOMALY_THRESHOLD

        self.total_scored += 1
        if is_anomalous:
            self.anomalies_detected += 1

        result = AnomalyScore(
            device_id=feature_vector.device_id, device_type=feature_vector.device_type,
            window_id=feature_vector.window_id, anomaly_score=anomaly_score,
            raw_score=round(raw_score, 4), is_anomalous=is_anomalous,
            threshold=ANOMALY_THRESHOLD,
            feature_contributions=self._compute_contributions(feature_vector, X_scaled),
            timestamp=datetime.now(timezone.utc),
        )
        self.scores_store[feature_vector.device_id].append(result)
        return result

    def score_batch(self, feature_vectors: list[DeviceFeatureVector]) -> list[AnomalyScore]:
        return [self.score(fv) for fv in feature_vectors]

    def get_device_scores(self, device_id: str) -> list[AnomalyScore]:
        return self.scores_store.get(device_id, [])

    def get_latest_scores(self) -> list[AnomalyScore]:
        return [scores[-1] for scores in self.scores_store.values() if scores]

    def get_anomalous_devices(self) -> list[AnomalyScore]:
        return [s for s in self.get_latest_scores() if s.is_anomalous]

    def get_model_info(self) -> Optional[MLModelInfo]:
        if not self.meta:
            return None
        return MLModelInfo(
            model_type=self.meta["model_type"], training_samples=self.meta["training_samples"],
            training_features=self.meta["training_features"], contamination=self.meta["contamination"],
            trained_at=datetime.fromisoformat(self.meta["trained_at"]),
            dataset_source=self.meta["dataset_source"],
            benign_samples=self.meta["benign_samples"], malicious_samples=self.meta["malicious_samples"],
        )
