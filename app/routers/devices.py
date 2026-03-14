import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import (
    AddDeviceRequest,
    AddDeviceResponse,
    BaselineOut,
    DeviceAnalyticsOut,
    DeviceDetail,
    DeviceSummary,
    DriftStateOut,
    ExplainResponse,
    FeatureStatOut,
    FeatureVectorOut,
    MLAnomalyOut,
    MLModelInfoOut,
    NetworkEdge,
    NetworkMap,
    NetworkNode,
    OverviewStats,
    PolicyStateOut,
    ProtectionStateOut,
    SignalBreakdownOut,
    TrustHistoryOut,
)
from app.services.trust_engine import (
    compute_risk_level,
    generate_open_ports,
    generate_protocol_usage,
    generate_security_explanation,
)
from app.services.ml_pipeline import pipeline

logger = logging.getLogger("iot_monitor.devices")
router = APIRouter()


async def _fetch_all_devices() -> list:
    result = await asyncio.to_thread(
        lambda: supabase.table("devices").select("*").execute()
    )
    return result.data or []


async def _fetch_device(device_id: str) -> dict:
    result = await asyncio.to_thread(
        lambda: supabase.table("devices").select("*").eq("id", device_id).execute()
    )
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return rows[0]


def _build_signal_breakdown(device_id: str) -> SignalBreakdownOut | None:
    d = pipeline.get_device_trust_detail(device_id)
    if not d:
        return None
    return SignalBreakdownOut(**{k: d[k] for k in SignalBreakdownOut.model_fields if k in d})


def _build_features(device_id: str) -> FeatureVectorOut | None:
    d = pipeline.get_device_features(device_id)
    return FeatureVectorOut(**d) if d else None


def _build_baseline(device_id: str) -> BaselineOut | None:
    d = pipeline.get_device_baseline(device_id)
    if not d:
        return None
    stats = {
        k: FeatureStatOut(**v) for k, v in d.get("feature_stats", {}).items()
    }
    return BaselineOut(
        windows_learned=d["windows_learned"],
        is_frozen=d["is_frozen"],
        last_updated=d["last_updated"],
        allowed_protocols=d["allowed_protocols"],
        expected_destination_types=d["expected_destination_types"],
        feature_stats=stats,
    )


def _build_drift(device_id: str) -> DriftStateOut | None:
    d = pipeline.get_device_drift(device_id)
    return DriftStateOut(**d) if d else None


def _build_policy(device_id: str) -> PolicyStateOut | None:
    d = pipeline.get_device_policy(device_id)
    return PolicyStateOut(**d) if d else None


def _build_ml(device_id: str) -> MLAnomalyOut | None:
    d = pipeline.get_device_ml_detail(device_id)
    return MLAnomalyOut(**d) if d else None


def _build_protection(device_id: str) -> ProtectionStateOut | None:
    d = pipeline.get_device_protection(device_id)
    return ProtectionStateOut(**d) if d else None


def _build_trust_history(device_id: str) -> TrustHistoryOut | None:
    d = pipeline.get_device_trust_history(device_id)
    return TrustHistoryOut(**d) if d else None


@router.get(
    "/overview",
    response_model=OverviewStats,
    summary="Dashboard overview counts",
)
async def get_overview():
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").select("risk_level,status").execute()
        )
        devices = result.data or []
    except Exception as exc:
        logger.exception("GET /overview — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    counts = {"SAFE": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0}
    online = offline = 0
    for d in devices:
        level = d.get("risk_level", "SAFE")
        if level == "COMPROMISED":
            counts["HIGH"] += 1
        elif level in counts:
            counts[level] += 1
        if d.get("status") == "online":
            online += 1
        else:
            offline += 1

    return OverviewStats(
        total_devices=len(devices),
        safe=counts["SAFE"],
        low=counts["LOW"],
        medium=counts["MEDIUM"],
        high=counts["HIGH"],
        online=online,
        offline=offline,
    )


@router.get(
    "/devices",
    response_model=List[DeviceSummary],
    summary="List all devices",
)
async def list_devices():
    try:
        devices = await _fetch_all_devices()
    except Exception as exc:
        logger.exception("GET /devices — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc
    return [DeviceSummary(**d) for d in devices]


@router.post(
    "/devices",
    response_model=AddDeviceResponse,
    status_code=201,
    summary="Add a new device",
)
async def add_device(body: AddDeviceRequest):
    trust_score = max(0, min(100, body.trust_score))
    risk_level = compute_risk_level(trust_score)
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "name": body.name,
        "device_type": body.device_type,
        "ip_address": body.ip_address,
        "vendor": body.vendor,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "traffic_rate": body.traffic_rate,
        "status": body.status,
        "last_seen": now,
        "created_at": now,
        "parent_id": body.parent_id,
    }
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").insert(row).execute()
        )
    except Exception as exc:
        logger.exception("POST /devices — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    created = result.data[0]
    logger.info("POST /devices — created device '%s' id=%s", created["name"], created["id"])
    return AddDeviceResponse(**created)


@router.get(
    "/devices/{device_id}",
    response_model=DeviceDetail,
    summary="Full device detail with all ML analytics",
    description=(
        "Returns everything: device info, open ports, protocol usage, security explanation, "
        "plus full ML analytics — signal breakdown, live feature vector, baseline stats, "
        "drift state, policy violations, ML anomaly scores with feature contributions, "
        "baseline protection state, and trust score trajectory."
    ),
)
async def get_device(device_id: str):
    try:
        device = await _fetch_device(device_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("GET /devices/%s — DB error", device_id)
        raise HTTPException(status_code=502, detail="Database error") from exc

    return DeviceDetail(
        **device,
        open_ports=generate_open_ports(device["device_type"]),
        protocol_usage=generate_protocol_usage(device["device_type"]),
        security_explanation=generate_security_explanation(device),
        signal_breakdown=_build_signal_breakdown(device_id),
        features=_build_features(device_id),
        drift=_build_drift(device_id),
        policy=_build_policy(device_id),
        ml_anomaly=_build_ml(device_id),
        protection=_build_protection(device_id),
        trust_history=_build_trust_history(device_id),
    )


@router.get(
    "/devices/{device_id}/analytics",
    response_model=DeviceAnalyticsOut,
    summary="Deep-dive ML analytics for a device",
    description=(
        "All ML engine data in one call: trust signals, live features, baseline, "
        "drift detection, policy compliance, IsolationForest scores, protection state, trust history."
    ),
)
async def device_analytics(device_id: str):
    try:
        await _fetch_device(device_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("GET /devices/%s/analytics — DB error", device_id)
        raise HTTPException(status_code=502, detail="Database error") from exc

    return DeviceAnalyticsOut(
        trust_detail=_build_signal_breakdown(device_id),
        features=_build_features(device_id),
        baseline=_build_baseline(device_id),
        drift=_build_drift(device_id),
        policy=_build_policy(device_id),
        ml_anomaly=_build_ml(device_id),
        protection=_build_protection(device_id),
        trust_history=_build_trust_history(device_id),
    )


@router.get(
    "/devices/{device_id}/features",
    response_model=FeatureVectorOut,
    summary="Live telemetry features",
    description=(
        "The 12 extracted features from the latest telemetry window: "
        "packet rate, session duration, bytes sent/received, traffic volume, "
        "destination entropy, protocol entropy, external connection ratio, etc."
    ),
)
async def device_features(device_id: str):
    result = _build_features(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No feature data available for this device")
    return result


@router.get(
    "/devices/{device_id}/baseline",
    response_model=BaselineOut,
    summary="Learned baseline profile",
    description=(
        "Statistical baseline for this device — mean, std, min, max for all 11 numeric features. "
        "This is what 'normal' looks like. Shows allowed protocols, expected destinations, "
        "and whether the baseline is frozen."
    ),
)
async def device_baseline(device_id: str):
    result = _build_baseline(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No baseline data available for this device")
    return result


@router.get(
    "/devices/{device_id}/drift",
    response_model=DriftStateOut,
    summary="Behavioral drift detection state",
    description=(
        "Is the device drifting from baseline? Shows severity, drift score, "
        "which features are drifting with z-scores, consecutive drift windows, "
        "confirmation status, and historical drift data."
    ),
)
async def device_drift(device_id: str):
    result = _build_drift(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No drift data available for this device")
    return result


@router.get(
    "/devices/{device_id}/policy",
    response_model=PolicyStateOut,
    summary="Policy compliance state",
    description=(
        "Is the device policy-compliant? Shows total violations, violation rate, "
        "violations by type (protocol blacklist, destination restriction, traffic ceiling, etc.), "
        "and the 10 most recent violation details with evidence."
    ),
)
async def device_policy(device_id: str):
    result = _build_policy(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No policy data available for this device")
    return result


@router.get(
    "/devices/{device_id}/ml",
    response_model=MLAnomalyOut,
    summary="ML anomaly detection detail",
    description=(
        "IsolationForest anomaly scores: current score, raw decision function score, "
        "is_anomalous flag, feature contributions showing which features are driving "
        "the anomaly, score history across all windows."
    ),
)
async def device_ml(device_id: str):
    result = _build_ml(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No ML data available for this device")
    return result


@router.get(
    "/devices/{device_id}/protection",
    response_model=ProtectionStateOut,
    summary="Baseline protection state",
    description=(
        "Anti-poisoning protection: is the baseline frozen or quarantined? "
        "Shows consecutive denials, poisoning attempts blocked, baseline integrity score, "
        "and gate decision history."
    ),
)
async def device_protection(device_id: str):
    result = _build_protection(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No protection data available for this device")
    return result


@router.get(
    "/devices/{device_id}/trust-history",
    response_model=TrustHistoryOut,
    summary="Trust score trajectory",
    description=(
        "Trust score over time: current, lowest, highest, average, "
        "and the full trajectory with risk level at each window."
    ),
)
async def device_trust_history(device_id: str):
    result = _build_trust_history(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="No trust history available for this device")
    return result


@router.get(
    "/devices/{device_id}/explain",
    response_model=ExplainResponse,
    summary="Security explanation with ML signals",
)
async def explain_device(device_id: str):
    try:
        device = await _fetch_device(device_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("GET /devices/%s/explain — DB error", device_id)
        raise HTTPException(status_code=502, detail="Database error") from exc

    return ExplainResponse(
        device_id=device["id"],
        device_name=device["name"],
        risk_level=device["risk_level"],
        trust_score=device["trust_score"],
        explanation=generate_security_explanation(device),
        signal_breakdown=_build_signal_breakdown(device_id),
    )


@router.get(
    "/trust-summary",
    summary="ML trust engine summary",
)
async def trust_summary():
    if not pipeline.is_trained:
        return {"error": "ML pipeline not initialized"}
    return pipeline.get_trust_summary()


@router.get(
    "/protection-summary",
    summary="Baseline protection summary",
)
async def protection_summary():
    if not pipeline.is_trained:
        return {"error": "ML pipeline not initialized"}
    return pipeline.get_protection_summary()


@router.get(
    "/ml-model",
    response_model=MLModelInfoOut,
    summary="ML model info",
    description=(
        "Details about the IsolationForest model: hyperparameters, training data, "
        "feature list, total scored, anomaly detection rate."
    ),
)
async def ml_model_info():
    if not pipeline.is_trained:
        raise HTTPException(status_code=503, detail="ML pipeline not initialized")
    info = pipeline.get_ml_model_info()
    if not info:
        raise HTTPException(status_code=503, detail="ML model not available")
    return MLModelInfoOut(**info)


@router.get(
    "/network-map",
    response_model=NetworkMap,
    summary="Network topology map",
)
async def get_network_map():
    try:
        devices = await _fetch_all_devices()
    except Exception as exc:
        logger.exception("GET /network-map — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    if not devices:
        return NetworkMap(nodes=[], edges=[])

    nodes = [
        NetworkNode(
            id=d["id"],
            name=d["name"],
            device_type=d["device_type"],
            risk_level=d["risk_level"],
            trust_score=d["trust_score"],
            status=d["status"],
        )
        for d in devices
    ]

    gateway = next((d for d in devices if d["device_type"] == "gateway"), devices[0])
    router_dev = next((d for d in devices if d["device_type"] == "router"), gateway)
    hub = next((d for d in devices if d["device_type"] == "hub"), router_dev)

    PARENT_MAP = {
        "gateway":    None,
        "router":     gateway["id"],
        "hub":        router_dev["id"],
        "camera":     hub["id"],
        "sensor":     hub["id"],
        "smart_tv":   hub["id"],
        "laptop":     router_dev["id"],
        "printer":    router_dev["id"],
        "thermostat": hub["id"],
        "smartphone": router_dev["id"],
    }

    edges = []
    for d in devices:
        parent_id = d.get("parent_id") or PARENT_MAP.get(d["device_type"], gateway["id"])
        if parent_id and parent_id != d["id"]:
            edges.append(NetworkEdge(source=parent_id, target=d["id"]))

    return NetworkMap(nodes=nodes, edges=edges)
