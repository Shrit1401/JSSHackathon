from __future__ import annotations

import math
from collections import Counter, defaultdict

from ..models import TelemetryRecord, DestinationType, DeviceFeatureVector, FeatureSummary

WINDOW_DURATION_SECONDS = 60.0

FEATURE_NAMES = [
    "packet_rate", "avg_session_duration", "total_bytes_sent",
    "total_bytes_received", "traffic_volume", "unique_destinations",
    "destination_entropy", "unique_protocols", "protocol_entropy",
    "protocol_distribution", "external_connection_ratio", "inbound_outbound_ratio",
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
    protocol_distribution = {proto: round(count / total_proto, 4) for proto, count in protocol_counts.items()}
    external_count = sum(1 for r in records if r.destination_type == DestinationType.UNKNOWN_EXTERNAL)
    external_connection_ratio = round(external_count / len(records), 4)
    inbound_outbound_ratio = round(total_bytes_received / max(total_bytes_sent, 1), 4)
    timestamps = [r.timestamp for r in records]

    return DeviceFeatureVector(
        device_id=device_id, device_type=device_type, window_id=window_id,
        packet_rate=packet_rate, avg_session_duration=avg_session_duration,
        total_bytes_sent=total_bytes_sent, total_bytes_received=total_bytes_received,
        traffic_volume=traffic_volume, unique_destinations=unique_destinations,
        destination_entropy=destination_entropy, unique_protocols=unique_protocols,
        protocol_entropy=protocol_entropy, protocol_distribution=protocol_distribution,
        external_connection_ratio=external_connection_ratio,
        inbound_outbound_ratio=inbound_outbound_ratio,
        record_count=len(records), window_start=min(timestamps), window_end=max(timestamps),
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
