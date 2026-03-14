import math
from collections import Counter, defaultdict
from typing import Optional

from app.models.telemetry import TelemetryRecord, DestinationType
from app.models.features import DeviceFeatureVector, DeviceFeatureTimeline, FeatureSummary

WINDOW_DURATION_SECONDS = 60.0

FEATURE_NAMES = [
    "packet_rate",
    "avg_session_duration",
    "total_bytes_sent",
    "total_bytes_received",
    "traffic_volume",
    "unique_destinations",
    "destination_entropy",
    "unique_protocols",
    "protocol_entropy",
    "protocol_distribution",
    "external_connection_ratio",
    "inbound_outbound_ratio",
]


def _shannon_entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def extract_features(device_id: str, records: list[TelemetryRecord], window_id: int) -> DeviceFeatureVector:
    if not records:
        raise ValueError(f"No records for device {device_id} in window {window_id}")

    device_type = records[0].device_type

    total_packets = sum(r.packet_count for r in records)
    packet_rate = round(total_packets / (WINDOW_DURATION_SECONDS / 60.0), 2)

    durations = [r.session_duration for r in records]
    avg_session_duration = round(sum(durations) / len(durations), 2)

    total_bytes_sent = sum(r.bytes_sent for r in records)
    total_bytes_received = sum(r.bytes_received for r in records)
    traffic_volume = total_bytes_sent + total_bytes_received

    destinations = [r.dst_ip for r in records]
    unique_destinations = len(set(destinations))
    destination_entropy = _shannon_entropy(destinations)

    protocols = [r.protocol.value for r in records]
    unique_protocols = len(set(protocols))
    protocol_entropy = _shannon_entropy(protocols)

    protocol_counts = Counter(protocols)
    total_proto = len(protocols)
    protocol_distribution = {
        proto: round(count / total_proto, 4) for proto, count in protocol_counts.items()
    }

    external_count = sum(1 for r in records if r.destination_type == DestinationType.UNKNOWN_EXTERNAL)
    external_connection_ratio = round(external_count / len(records), 4)

    inbound_outbound_ratio = round(
        total_bytes_received / max(total_bytes_sent, 1), 4
    )

    timestamps = [r.timestamp for r in records]
    window_start = min(timestamps)
    window_end = max(timestamps)

    return DeviceFeatureVector(
        device_id=device_id,
        device_type=device_type,
        window_id=window_id,
        packet_rate=packet_rate,
        avg_session_duration=avg_session_duration,
        total_bytes_sent=total_bytes_sent,
        total_bytes_received=total_bytes_received,
        traffic_volume=traffic_volume,
        unique_destinations=unique_destinations,
        destination_entropy=destination_entropy,
        unique_protocols=unique_protocols,
        protocol_entropy=protocol_entropy,
        protocol_distribution=protocol_distribution,
        external_connection_ratio=external_connection_ratio,
        inbound_outbound_ratio=inbound_outbound_ratio,
        record_count=len(records),
        window_start=window_start,
        window_end=window_end,
    )


class FeatureEngine:
    def __init__(self):
        self.feature_store: dict[str, dict[int, DeviceFeatureVector]] = defaultdict(dict)

    def process_window(self, records: list[TelemetryRecord]) -> list[DeviceFeatureVector]:
        by_device: dict[str, list[TelemetryRecord]] = defaultdict(list)
        for r in records:
            by_device[r.device_id].append(r)

        window_features = []
        for device_id, device_records in by_device.items():
            window_id = device_records[0].window_id or 0
            fv = extract_features(device_id, device_records, window_id)
            self.feature_store[device_id][window_id] = fv
            window_features.append(fv)

        return window_features

    def process_all_windows(self, records: list[TelemetryRecord]) -> list[DeviceFeatureVector]:
        by_device_window: dict[tuple[str, int], list[TelemetryRecord]] = defaultdict(list)
        for r in records:
            key = (r.device_id, r.window_id or 0)
            by_device_window[key].append(r)

        all_features = []
        for (device_id, window_id), device_records in sorted(by_device_window.items(), key=lambda x: x[0]):
            fv = extract_features(device_id, device_records, window_id)
            self.feature_store[device_id][window_id] = fv
            all_features.append(fv)

        return all_features

    def get_device_features(self, device_id: str) -> list[DeviceFeatureVector]:
        if device_id not in self.feature_store:
            return []
        return [self.feature_store[device_id][w] for w in sorted(self.feature_store[device_id])]

    def get_device_timeline(self, device_id: str) -> Optional[DeviceFeatureTimeline]:
        features = self.get_device_features(device_id)
        if not features:
            return None
        return DeviceFeatureTimeline(
            device_id=device_id,
            device_type=features[0].device_type,
            windows=features,
            total_windows=len(features),
        )

    def get_window_features(self, window_id: int) -> list[DeviceFeatureVector]:
        results = []
        for device_id, windows in self.feature_store.items():
            if window_id in windows:
                results.append(windows[window_id])
        return results

    def get_latest_features(self) -> list[DeviceFeatureVector]:
        latest = []
        for device_id, windows in self.feature_store.items():
            if windows:
                max_window = max(windows.keys())
                latest.append(windows[max_window])
        return latest

    def get_summary(self) -> FeatureSummary:
        total_features = sum(len(w) for w in self.feature_store.values())
        all_windows = set()
        for windows in self.feature_store.values():
            all_windows.update(windows.keys())

        return FeatureSummary(
            total_devices=len(self.feature_store),
            total_windows=len(all_windows),
            features_computed=total_features,
            feature_names=FEATURE_NAMES,
        )

    def reset(self):
        self.feature_store.clear()
