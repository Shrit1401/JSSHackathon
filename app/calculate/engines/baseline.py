from __future__ import annotations

import math
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional

from ..models import (
    DeviceType, DeviceFeatureVector, FeatureStats,
    DeviceBaseline, DeviceTypeBaseline, BaselineDeviation,
)
from ..device_profiles import DEVICE_PROFILES

NUMERIC_FEATURES = [
    "packet_rate", "avg_session_duration", "traffic_volume",
    "total_bytes_sent", "total_bytes_received", "destination_entropy",
    "protocol_entropy", "unique_destinations", "unique_protocols",
    "external_connection_ratio", "inbound_outbound_ratio",
]

TRAFFIC_DIRECTIONS = {
    DeviceType.CAMERA: "high_outbound",
    DeviceType.PRINTER: "balanced_low",
    DeviceType.ROUTER: "balanced_symmetric",
    DeviceType.LAPTOP: "balanced_variable",
    DeviceType.SMART_TV: "high_inbound",
}


def _compute_stats(values: list[float]) -> FeatureStats:
    n = len(values)
    if n == 0:
        return FeatureStats(mean=0.0, std=0.0, min_val=0.0, max_val=0.0, samples=0)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)
    std = max(std, mean * 0.01) if mean > 0 else max(std, 0.001)
    return FeatureStats(
        mean=round(mean, 4), std=round(std, 4),
        min_val=round(min(values), 4), max_val=round(max(values), 4), samples=n,
    )


def _collect_protocols(features: list[DeviceFeatureVector]) -> list[str]:
    protos = set()
    for fv in features:
        protos.update(fv.protocol_distribution.keys())
    return sorted(protos)


def _collect_destination_types(device_type: DeviceType) -> list[str]:
    profile = DEVICE_PROFILES[device_type]
    return [d.value for d in profile["normal_destinations"]]


class BaselineEngine:
    def __init__(self):
        self.device_baselines: dict[str, DeviceBaseline] = {}
        self.type_baselines: dict[DeviceType, DeviceTypeBaseline] = {}
        self.baseline_windows = 0

    def learn_device_baseline(self, device_id: str, device_type: DeviceType, features: list[DeviceFeatureVector]) -> DeviceBaseline:
        if not features:
            raise ValueError(f"No features to learn baseline for {device_id}")
        stats = {}
        for feat in NUMERIC_FEATURES:
            values = [getattr(fv, feat) for fv in features]
            stats[feat] = _compute_stats(values)

        baseline = DeviceBaseline(
            device_id=device_id, device_type=device_type,
            windows_learned=len(features), last_updated=datetime.now(timezone.utc),
            allowed_protocols=_collect_protocols(features),
            expected_destination_types=_collect_destination_types(device_type),
            **stats,
        )
        self.device_baselines[device_id] = baseline
        return baseline

    def learn_type_baseline(self, device_type: DeviceType, features: list[DeviceFeatureVector]) -> DeviceTypeBaseline:
        if not features:
            raise ValueError(f"No features to learn baseline for {device_type.value}")
        device_ids = set(fv.device_id for fv in features)
        stats = {}
        for feat in NUMERIC_FEATURES:
            values = [getattr(fv, feat) for fv in features]
            stats[feat] = _compute_stats(values)

        baseline = DeviceTypeBaseline(
            device_type=device_type, device_count=len(device_ids),
            total_windows=len(features), last_updated=datetime.now(timezone.utc),
            allowed_protocols=_collect_protocols(features),
            expected_destination_types=_collect_destination_types(device_type),
            traffic_direction=TRAFFIC_DIRECTIONS.get(device_type, "unknown"),
            **stats,
        )
        self.type_baselines[device_type] = baseline
        return baseline

    def learn_all_baselines(self, all_features: list[DeviceFeatureVector]) -> dict:
        by_device: dict[str, list[DeviceFeatureVector]] = defaultdict(list)
        by_type: dict[DeviceType, list[DeviceFeatureVector]] = defaultdict(list)
        for fv in all_features:
            by_device[fv.device_id].append(fv)
            by_type[fv.device_type].append(fv)

        for device_id, features in by_device.items():
            self.learn_device_baseline(device_id, features[0].device_type, features)
        for device_type, features in by_type.items():
            self.learn_type_baseline(device_type, features)

        self.baseline_windows = len(set(fv.window_id for fv in all_features))
        return {
            "device_baselines": len(self.device_baselines),
            "type_baselines": len(self.type_baselines),
            "windows_used": self.baseline_windows,
        }

    def compute_deviation(self, feature_vector: DeviceFeatureVector, threshold: float = 2.5) -> BaselineDeviation:
        device_id = feature_vector.device_id
        baseline = self.device_baselines.get(device_id)
        if not baseline:
            type_bl = self.type_baselines.get(feature_vector.device_type)
            if not type_bl:
                raise ValueError(f"No baseline found for {device_id} or type {feature_vector.device_type.value}")
            baseline = type_bl

        deviations = {}
        for feat in NUMERIC_FEATURES:
            current = getattr(feature_vector, feat)
            stats: FeatureStats = getattr(baseline, feat)
            if stats.std > 0:
                z = (current - stats.mean) / stats.std
            else:
                z = 0.0 if current == stats.mean else 10.0
            deviations[feat] = round(z, 4)

        abs_devs = {k: abs(v) for k, v in deviations.items()}
        max_feat = max(abs_devs, key=abs_devs.get)
        beyond = [f for f, z in abs_devs.items() if z > threshold]

        return BaselineDeviation(
            device_id=feature_vector.device_id, device_type=feature_vector.device_type,
            window_id=feature_vector.window_id, deviations=deviations,
            max_deviation_feature=max_feat, max_deviation_zscore=round(abs_devs[max_feat], 4),
            features_beyond_threshold=beyond, threshold_used=threshold,
        )

    def update_device_baseline(self, device_id: str, new_feature: DeviceFeatureVector) -> bool:
        baseline = self.device_baselines.get(device_id)
        if not baseline or baseline.is_frozen:
            return False

        n = baseline.windows_learned
        for feat in NUMERIC_FEATURES:
            stats: FeatureStats = getattr(baseline, feat)
            new_val = getattr(new_feature, feat)
            new_mean = (stats.mean * n + new_val) / (n + 1)
            new_var = (n * (stats.std ** 2 + (stats.mean - new_mean) ** 2) + (new_val - new_mean) ** 2) / (n + 1)
            new_std = max(math.sqrt(new_var), new_mean * 0.01) if new_mean > 0 else max(math.sqrt(new_var), 0.001)
            updated = FeatureStats(
                mean=round(new_mean, 4), std=round(new_std, 4),
                min_val=round(min(stats.min_val, new_val), 4),
                max_val=round(max(stats.max_val, new_val), 4), samples=n + 1,
            )
            setattr(baseline, feat, updated)

        new_protos = set(baseline.allowed_protocols)
        new_protos.update(new_feature.protocol_distribution.keys())
        baseline.allowed_protocols = sorted(new_protos)
        baseline.windows_learned = n + 1
        baseline.last_updated = datetime.now(timezone.utc)
        return True

    def freeze_device(self, device_id: str) -> bool:
        if device_id in self.device_baselines:
            self.device_baselines[device_id].is_frozen = True
            return True
        return False

    def unfreeze_device(self, device_id: str) -> bool:
        if device_id in self.device_baselines:
            self.device_baselines[device_id].is_frozen = False
            return True
        return False

    def get_device_baseline(self, device_id: str) -> Optional[DeviceBaseline]:
        return self.device_baselines.get(device_id)

    def get_type_baseline(self, device_type: DeviceType) -> Optional[DeviceTypeBaseline]:
        return self.type_baselines.get(device_type)
