import os
import pickle
from datetime import datetime
from typing import Optional
from collections import defaultdict

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.models.telemetry import DeviceType
from app.models.features import DeviceFeatureVector
from app.models.ml import AnomalyScore, MLModelInfo, MLSummary

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")
META_PATH = os.path.join(ARTIFACTS_DIR, "model_meta.pkl")

INPUT_FEATURES = [
    "packet_rate",
    "avg_session_duration",
    "total_bytes_sent",
    "total_bytes_received",
    "destination_entropy",
    "protocol_entropy",
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
            n_estimators=200,
            contamination=0.01,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)

        raw_scores = self.model.decision_function(X_scaled)
        self._baseline_mean_score = float(np.mean(raw_scores))
        self._baseline_std_score = max(float(np.std(raw_scores)), 0.001)

        csv_meta = None
        try:
            with open(META_PATH, "rb") as f:
                csv_meta = pickle.load(f)
        except FileNotFoundError:
            pass

        self.meta = {
            "model_type": "IsolationForest",
            "n_estimators": 200,
            "contamination": 0.01,
            "training_samples": len(baseline_features),
            "training_features": INPUT_FEATURES,
            "trained_at": datetime.utcnow().isoformat(),
            "dataset_source": "baseline_telemetry" + (" + dataset.csv" if csv_meta else ""),
            "benign_samples": len(baseline_features),
            "malicious_samples": csv_meta["malicious_samples"] if csv_meta else 0,
        }

    def _features_to_matrix(self, features: list[DeviceFeatureVector]) -> np.ndarray:
        rows = []
        for fv in features:
            rows.append([getattr(fv, feat) for feat in INPUT_FEATURES])
        return np.array(rows, dtype=np.float64)

    def _feature_vector_to_array(self, fv: DeviceFeatureVector) -> np.ndarray:
        values = [getattr(fv, feat) for feat in INPUT_FEATURES]
        return np.array(values, dtype=np.float64).reshape(1, -1)

    def _raw_to_anomaly_score(self, raw_score: float) -> float:
        z = (self._baseline_mean_score - raw_score) / self._baseline_std_score
        score = 1.0 / (1.0 + np.exp(-z))
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    def _compute_contributions(self, fv: DeviceFeatureVector, scaled: np.ndarray) -> dict[str, float]:
        contributions = {}
        for i, feat in enumerate(INPUT_FEATURES):
            abs_val = abs(float(scaled[0, i]))
            contributions[feat] = round(abs_val, 4)

        total = sum(contributions.values())
        if total > 0:
            contributions = {k: round(v / total, 4) for k, v in contributions.items()}

        return contributions

    def score(self, feature_vector: DeviceFeatureVector) -> AnomalyScore:
        if not self.model or not self.scaler:
            raise RuntimeError("ML model not loaded. Run training first.")

        X = self._feature_vector_to_array(feature_vector)
        np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)

        X_scaled = self.scaler.transform(X)
        raw_score = float(self.model.decision_function(X_scaled)[0])
        anomaly_score = self._raw_to_anomaly_score(raw_score)
        is_anomalous = anomaly_score >= ANOMALY_THRESHOLD

        contributions = self._compute_contributions(feature_vector, X_scaled)

        self.total_scored += 1
        if is_anomalous:
            self.anomalies_detected += 1

        result = AnomalyScore(
            device_id=feature_vector.device_id,
            device_type=feature_vector.device_type,
            window_id=feature_vector.window_id,
            anomaly_score=anomaly_score,
            raw_score=round(raw_score, 4),
            is_anomalous=is_anomalous,
            threshold=ANOMALY_THRESHOLD,
            feature_contributions=contributions,
            timestamp=datetime.utcnow(),
        )

        self.scores_store[feature_vector.device_id].append(result)
        return result

    def score_batch(self, feature_vectors: list[DeviceFeatureVector]) -> list[AnomalyScore]:
        return [self.score(fv) for fv in feature_vectors]

    def get_device_scores(self, device_id: str) -> list[AnomalyScore]:
        return self.scores_store.get(device_id, [])

    def get_latest_scores(self) -> list[AnomalyScore]:
        latest = []
        for device_id, scores in self.scores_store.items():
            if scores:
                latest.append(scores[-1])
        return latest

    def get_anomalous_devices(self) -> list[AnomalyScore]:
        return [s for s in self.get_latest_scores() if s.is_anomalous]

    def get_model_info(self) -> Optional[MLModelInfo]:
        if not self.meta:
            return None
        return MLModelInfo(
            model_type=self.meta["model_type"],
            training_samples=self.meta["training_samples"],
            training_features=self.meta["training_features"],
            contamination=self.meta["contamination"],
            trained_at=datetime.fromisoformat(self.meta["trained_at"]),
            dataset_source=self.meta["dataset_source"],
            benign_samples=self.meta["benign_samples"],
            malicious_samples=self.meta["malicious_samples"],
        )

    def get_summary(self) -> MLSummary:
        rate = self.anomalies_detected / max(self.total_scored, 1)
        return MLSummary(
            model_loaded=self.model is not None,
            model_info=self.get_model_info(),
            total_scored=self.total_scored,
            anomalies_detected=self.anomalies_detected,
            anomaly_rate=round(rate, 4),
        )

    def reset(self):
        self.scores_store.clear()
        self.total_scored = 0
        self.anomalies_detected = 0
