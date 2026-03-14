from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.database.client import supabase

logger = logging.getLogger("iot_sentinel.db")

_db_available = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _safe_execute(fn, fallback=None):
    global _db_available
    try:
        return fn()
    except Exception as e:
        logger.warning(f"Supabase call failed: {e}")
        return fallback


# ═══════════════════════════════════════════
#  DEVICES
# ═══════════════════════════════════════════

def upsert_device(
    device_name: str,
    device_type: str,
    ip_address: str,
    mac_address: str | None = None,
    manufacturer: str | None = None,
    firmware_version: str | None = None,
    trust_score: float = 100.0,
    risk_level: str = "SAFE",
    status: str = "safe",
    device_id: str | None = None,
) -> dict:
    row = {
        "id": device_id or _uuid(),
        "device_name": device_name,
        "device_type": device_type,
        "ip_address": ip_address,
        "mac_address": mac_address,
        "manufacturer": manufacturer,
        "firmware_version": firmware_version,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "status": status,
        "last_seen": _now(),
    }
    def _do():
        resp = supabase.table("devices").upsert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def get_device(device_id: str) -> dict | None:
    def _do():
        resp = supabase.table("devices").select("*").eq("id", device_id).execute()
        return resp.data[0] if resp.data else None
    return _safe_execute(_do)


def get_all_devices() -> list[dict]:
    def _do():
        resp = supabase.table("devices").select("*").order("device_name").execute()
        return resp.data or []
    return _safe_execute(_do, fallback=[])


def update_device_trust(device_id: str, trust_score: float, risk_level: str, status: str) -> dict | None:
    def _do():
        resp = (
            supabase.table("devices")
            .update({
                "trust_score": trust_score,
                "risk_level": risk_level,
                "status": status,
                "last_seen": _now(),
            })
            .eq("id", device_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    return _safe_execute(_do)


def update_device_last_seen(device_id: str) -> None:
    _safe_execute(lambda: supabase.table("devices").update({"last_seen": _now()}).eq("id", device_id).execute())


# ═══════════════════════════════════════════
#  TELEMETRY EVENTS
# ═══════════════════════════════════════════

def insert_telemetry(
    device_id: str,
    protocol: str,
    bytes_sent: int = 0,
    bytes_received: int = 0,
    packet_count: int = 0,
    session_duration: float = 0.0,
    destination_ip: str | None = None,
    destination_type: str | None = None,
    timestamp: str | None = None,
) -> dict:
    row = {
        "id": _uuid(),
        "device_id": device_id,
        "protocol": protocol,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "packet_count": packet_count,
        "session_duration": session_duration,
        "destination_ip": destination_ip,
        "destination_type": destination_type,
        "timestamp": timestamp or _now(),
    }
    def _do():
        resp = supabase.table("telemetry_events").insert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def insert_telemetry_batch(rows: list[dict]) -> list[dict]:
    for r in rows:
        r.setdefault("id", _uuid())
        r.setdefault("timestamp", _now())
    def _do():
        resp = supabase.table("telemetry_events").insert(rows).execute()
        return resp.data or rows
    return _safe_execute(_do, fallback=rows)


def get_telemetry_for_device(device_id: str, limit: int = 100) -> list[dict]:
    def _do():
        resp = (
            supabase.table("telemetry_events")
            .select("*")
            .eq("device_id", device_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    return _safe_execute(_do, fallback=[])


# ═══════════════════════════════════════════
#  DEVICE FEATURES
# ═══════════════════════════════════════════

def insert_features(
    device_id: str,
    packet_rate: float,
    avg_session_duration: float,
    traffic_volume: int,
    destination_entropy: float,
    protocol_entropy: float,
) -> dict:
    row = {
        "id": _uuid(),
        "device_id": device_id,
        "packet_rate": packet_rate,
        "avg_session_duration": avg_session_duration,
        "traffic_volume": traffic_volume,
        "destination_entropy": destination_entropy,
        "protocol_entropy": protocol_entropy,
        "calculated_at": _now(),
    }
    def _do():
        resp = supabase.table("device_features").insert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def get_latest_features(device_id: str) -> dict | None:
    def _do():
        resp = (
            supabase.table("device_features")
            .select("*")
            .eq("device_id", device_id)
            .order("calculated_at", desc=True)
            .limit(1)
            .execute()
        )
        return resp.data[0] if resp.data else None
    return _safe_execute(_do)


# ═══════════════════════════════════════════
#  ALERTS
# ═══════════════════════════════════════════

def insert_alert(
    device_id: str,
    alert_type: str,
    severity: str,
    description: str = "",
    confidence: float = 0.0,
    resolved: bool = False,
) -> dict:
    row = {
        "id": _uuid(),
        "device_id": device_id,
        "alert_type": alert_type,
        "severity": severity,
        "description": description,
        "confidence": confidence,
        "timestamp": _now(),
        "resolved": resolved,
    }
    def _do():
        resp = supabase.table("alerts").insert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def get_alerts(
    device_id: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> list[dict]:
    def _do():
        query = supabase.table("alerts").select("*")
        if device_id:
            query = query.eq("device_id", device_id)
        if severity:
            query = query.eq("severity", severity)
        resp = query.order("timestamp", desc=True).limit(limit).execute()
        return resp.data or []
    return _safe_execute(_do, fallback=[])


def resolve_alert(alert_id: str) -> dict | None:
    def _do():
        resp = (
            supabase.table("alerts")
            .update({"resolved": True})
            .eq("id", alert_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    return _safe_execute(_do)


# ═══════════════════════════════════════════
#  TRUST HISTORY
# ═══════════════════════════════════════════

def insert_trust_history(
    device_id: str,
    trust_score: float,
    reason: str = "",
    timestamp: str | None = None,
) -> dict:
    row = {
        "id": _uuid(),
        "device_id": device_id,
        "trust_score": trust_score,
        "reason": reason,
        "timestamp": timestamp or _now(),
    }
    def _do():
        resp = supabase.table("trust_history").insert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def get_trust_history(device_id: str, limit: int = 100) -> list[dict]:
    def _do():
        resp = (
            supabase.table("trust_history")
            .select("*")
            .eq("device_id", device_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    return _safe_execute(_do, fallback=[])


# ═══════════════════════════════════════════
#  NETWORK TOPOLOGY
# ═══════════════════════════════════════════

def upsert_topology(
    source_device: str,
    target_device: str,
    connection_type: str = "ethernet",
    edge_id: str | None = None,
) -> dict:
    row = {
        "id": edge_id or _uuid(),
        "source_device": source_device,
        "target_device": target_device,
        "connection_type": connection_type,
        "last_active": _now(),
    }
    def _do():
        resp = supabase.table("network_topology").upsert(row).execute()
        return resp.data[0] if resp.data else row
    return _safe_execute(_do, fallback=row)


def get_full_topology() -> list[dict]:
    def _do():
        resp = supabase.table("network_topology").select("*").execute()
        return resp.data or []
    return _safe_execute(_do, fallback=[])


def get_network_map() -> dict:
    devices = get_all_devices()
    edges = get_full_topology()

    nodes = [
        {
            "id": d["id"],
            "device_name": d["device_name"],
            "device_type": d["device_type"],
            "ip_address": d["ip_address"],
            "trust_score": d["trust_score"],
            "risk_level": d["risk_level"],
            "status": d["status"],
        }
        for d in devices
    ]

    links = [
        {
            "id": e["id"],
            "source": e["source_device"],
            "target": e["target_device"],
            "connection_type": e["connection_type"],
            "last_active": e["last_active"],
        }
        for e in edges
    ]

    return {"nodes": nodes, "edges": links}


# ═══════════════════════════════════════════
#  SEED / BOOTSTRAP
# ═══════════════════════════════════════════

def seed_device_fleet(profiles: list[dict]) -> list[dict]:
    created = []
    for p in profiles:
        d = upsert_device(**p)
        created.append(d)
    return created


def persist_ml_results(
    device_id: str,
    trust_score: float,
    risk_level: str,
    reason: str,
    anomaly_score: float = 0.0,
    drift_score: float = 0.0,
    policy_violation: bool = False,
    alert_threshold: float = 60.0,
) -> dict:
    status = "safe"
    if trust_score < 40:
        status = "compromised"
    elif trust_score < 70:
        status = "suspicious"

    update_device_trust(device_id, trust_score, risk_level, status)
    insert_trust_history(device_id, trust_score, reason)

    alert_created = None
    if trust_score < alert_threshold:
        severity = "CRITICAL" if trust_score < 40 else "HIGH"
        alert_created = insert_alert(
            device_id=device_id,
            alert_type="TRUST_DROP",
            severity=severity,
            description=f"Trust dropped to {trust_score:.1f} — {reason}",
            confidence=1.0 - (trust_score / 100.0),
        )

    return {
        "device_id": device_id,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "status": status,
        "alert_created": alert_created is not None,
    }
