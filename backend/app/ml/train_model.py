import csv
import math
import os
import pickle
from datetime import datetime
from collections import Counter, defaultdict

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
META_PATH = os.path.join(MODEL_DIR, "model_meta.pkl")

FEATURE_NAMES = [
    "packet_rate",
    "avg_session_duration",
    "total_bytes_sent",
    "total_bytes_received",
    "destination_entropy",
    "protocol_entropy",
]

WINDOW_SECONDS = 60


def _shannon_entropy(values):
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    ent = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            ent -= p * math.log2(p)
    return round(ent, 4)


def load_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)


def window_records(rows):
    for r in rows:
        ts_str = r["timestamp"][:26]
        r["_ts"] = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
        r["_duration"] = float(r["duration"]) if r["duration"] else 0.0
        r["_orig"] = float(r["orig_bytes"]) if r["orig_bytes"] else 0.0
        r["_resp"] = float(r["resp_bytes"]) if r["resp_bytes"] else 0.0

    rows.sort(key=lambda r: r["_ts"])
    windows = []
    current_window = []
    window_start = rows[0]["_ts"]

    for r in rows:
        if (r["_ts"] - window_start).total_seconds() > WINDOW_SECONDS:
            if current_window:
                windows.append(current_window)
            current_window = [r]
            window_start = r["_ts"]
        else:
            current_window.append(r)

    if current_window:
        windows.append(current_window)

    return windows


def extract_window_features(window):
    n = len(window)
    packet_rate = float(n)
    avg_duration = sum(r["_duration"] for r in window) / max(n, 1)
    total_sent = sum(r["_orig"] for r in window)
    total_recv = sum(r["_resp"] for r in window)
    dest_entropy = _shannon_entropy([r["dst_ip"] for r in window])
    proto_entropy = _shannon_entropy([r["proto"] for r in window])

    return [packet_rate, avg_duration, total_sent, total_recv, dest_entropy, proto_entropy]


def extract_labels(window):
    malicious_count = sum(1 for r in window if r["label"] == "Malicious")
    return 1 if malicious_count > len(window) * 0.5 else 0


def train():
    print("Loading dataset...")
    rows = load_csv(DATASET_PATH)
    print(f"  {len(rows)} records loaded")

    benign = sum(1 for r in rows if r["label"] == "Benign")
    malicious = sum(1 for r in rows if r["label"] == "Malicious")
    print(f"  Benign: {benign}, Malicious: {malicious}")

    print("Windowing records...")
    windows = window_records(rows)
    print(f"  {len(windows)} windows created")

    print("Extracting features...")
    X = []
    y = []
    for w in windows:
        features = extract_window_features(w)
        label = extract_labels(w)
        X.append(features)
        y.append(label)

    X = np.array(X, dtype=np.float64)
    y = np.array(y)
    print(f"  Feature matrix: {X.shape}")
    print(f"  Normal windows: {np.sum(y == 0)}, Anomalous windows: {np.sum(y == 1)}")

    np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)

    print("Fitting scaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    contamination = float(np.sum(y == 1)) / len(y)
    contamination = max(0.01, min(contamination, 0.5))
    print(f"  Contamination rate: {contamination:.4f}")

    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)
    anomalies_detected = np.sum(predictions == -1)
    print(f"  Training anomalies detected: {anomalies_detected}/{len(predictions)}")

    true_pos = np.sum((predictions == -1) & (y == 1))
    true_neg = np.sum((predictions == 1) & (y == 0))
    false_pos = np.sum((predictions == -1) & (y == 0))
    false_neg = np.sum((predictions == 1) & (y == 1))
    accuracy = (true_pos + true_neg) / len(y) if len(y) > 0 else 0
    print(f"  TP={true_pos} TN={true_neg} FP={false_pos} FN={false_neg}")
    print(f"  Accuracy: {accuracy:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"  Model saved to {MODEL_PATH}")

    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  Scaler saved to {SCALER_PATH}")

    meta = {
        "model_type": "IsolationForest",
        "n_estimators": 200,
        "contamination": contamination,
        "training_samples": len(X),
        "training_features": FEATURE_NAMES,
        "trained_at": datetime.utcnow().isoformat(),
        "dataset_source": "dataset.csv",
        "benign_samples": int(np.sum(y == 0)),
        "malicious_samples": int(np.sum(y == 1)),
        "accuracy": accuracy,
        "feature_means": scaler.mean_.tolist(),
        "feature_stds": scaler.scale_.tolist(),
    }
    with open(META_PATH, "wb") as f:
        pickle.dump(meta, f)
    print(f"  Metadata saved to {META_PATH}")

    print("\nTraining complete.")
    return model, scaler, meta


if __name__ == "__main__":
    train()
