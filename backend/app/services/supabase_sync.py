from __future__ import annotations

import uuid
from typing import Optional

from app.database import service as db
from app.models.telemetry import TelemetryRecord, DeviceState
from app.models.features import DeviceFeatureVector
from app.models.trust import DeviceTrustScore, RiskLevel
from app.models.alerts import Alert


TRUST_ALERT_THRESHOLD = 60.0

_device_uuid_map: dict[str, str] = {}


def _resolve_device_uuid(internal_id: str) -> str | None:
    return _device_uuid_map.get(internal_id)


def sync_devices(devices: list[DeviceState]) -> list[dict]:
    results = []
    for d in devices:
        existing_uuid = _device_uuid_map.get(d.device_id)
        row = db.upsert_device(
            device_id=existing_uuid or str(uuid.uuid4()),
            device_name=d.device_id,
            device_type=d.device_type.value,
            ip_address=d.ip_address,
            trust_score=100.0,
            risk_level="SAFE",
            status="compromised" if d.is_compromised else "safe",
        )
        _device_uuid_map[d.device_id] = row["id"]
        results.append(row)
    return results


def sync_telemetry_batch(records: list[TelemetryRecord]) -> int:
    rows = []
    for r in records:
        dev_uuid = _resolve_device_uuid(r.device_id)
        if not dev_uuid:
            continue
        dest_type_mapped = r.destination_type.value
        if dest_type_mapped == "unknown_external":
            dest_type_mapped = "external"
        rows.append({
            "device_id": dev_uuid,
            "protocol": r.protocol.value,
            "bytes_sent": r.bytes_sent,
            "bytes_received": r.bytes_received,
            "packet_count": r.packet_count,
            "session_duration": r.session_duration,
            "destination_ip": r.dst_ip,
            "destination_type": dest_type_mapped,
            "timestamp": r.timestamp.isoformat(),
        })
    if rows:
        db.insert_telemetry_batch(rows)
    return len(rows)


def sync_features(features: list[DeviceFeatureVector]) -> int:
    count = 0
    for fv in features:
        dev_uuid = _resolve_device_uuid(fv.device_id)
        if not dev_uuid:
            continue
        db.insert_features(
            device_id=dev_uuid,
            packet_rate=fv.packet_rate,
            avg_session_duration=fv.avg_session_duration,
            traffic_volume=fv.traffic_volume,
            destination_entropy=fv.destination_entropy,
            protocol_entropy=fv.protocol_entropy,
        )
        count += 1
    return count


def sync_trust_scores(scores: list[DeviceTrustScore]) -> list[dict]:
    results = []
    for s in scores:
        dev_uuid = _resolve_device_uuid(s.device_id)
        if not dev_uuid:
            continue

        status = "safe"
        if s.trust_score < 40:
            status = "compromised"
        elif s.trust_score < 70:
            status = "suspicious"

        breakdown = s.signal_breakdown
        reason_parts = []
        if breakdown.ml_penalty > 0:
            reason_parts.append(f"ml_penalty={breakdown.ml_penalty:.1f}")
        if breakdown.drift_penalty > 0:
            reason_parts.append(f"drift_penalty={breakdown.drift_penalty:.1f}")
        if breakdown.policy_penalty > 0:
            reason_parts.append(f"policy_penalty={breakdown.policy_penalty:.1f}")
        reason = ", ".join(reason_parts) or "nominal"

        result = db.persist_ml_results(
            device_id=dev_uuid,
            trust_score=s.trust_score,
            risk_level=s.risk_level.value,
            reason=reason,
            anomaly_score=breakdown.ml_anomaly_score,
            drift_score=breakdown.drift_score,
            policy_violation=breakdown.policy_violations_total > 0,
            alert_threshold=TRUST_ALERT_THRESHOLD,
        )
        results.append(result)
    return results


def sync_alert(alert: Alert) -> dict:
    dev_uuid = _resolve_device_uuid(alert.device_id)
    if not dev_uuid:
        return {}
    return db.insert_alert(
        device_id=dev_uuid,
        alert_type=alert.alert_type.value,
        severity=alert.severity.value,
        description=alert.reason,
        confidence=alert.trust_score_at_time or 0.0,
    )


def sync_alerts_batch(alerts: list[Alert]) -> int:
    count = 0
    for a in alerts:
        result = sync_alert(a)
        if result:
            count += 1
    return count


def build_topology_from_telemetry(records: list[TelemetryRecord]) -> int:
    seen_edges: set[tuple[str, str]] = set()
    count = 0

    for r in records:
        src_uuid = _resolve_device_uuid(r.device_id)
        if not src_uuid:
            continue

        for other_id, other_uuid in _device_uuid_map.items():
            if other_id == r.device_id:
                continue
            edge_key = tuple(sorted([src_uuid, other_uuid]))
            if edge_key in seen_edges:
                continue

            if r.destination_type.value == "internal":
                seen_edges.add(edge_key)
                db.upsert_topology(
                    source_device=src_uuid,
                    target_device=other_uuid,
                    connection_type="ethernet",
                )
                count += 1

    return count


def get_device_uuid_map() -> dict[str, str]:
    return dict(_device_uuid_map)
