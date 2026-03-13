import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import (
    AddDeviceRequest,
    AddDeviceResponse,
    DeviceDetail,
    DeviceSummary,
    ExplainResponse,
    NetworkEdge,
    NetworkMap,
    NetworkNode,
    OverviewStats,
)
from app.services.trust_engine import (
    compute_risk_level,
    generate_open_ports,
    generate_protocol_usage,
    generate_security_explanation,
)

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


# ---------------------------------------------------------------------------

@router.get(
    "/overview",
    response_model=OverviewStats,
    summary="Dashboard overview counts",
    description="Returns total device count broken down by risk level and online/offline status.",
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
        if level in counts:
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
    description="Returns every registered IoT device with its current trust score and risk level.",
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
    description=(
        "Registers a new IoT device. trust_score defaults to 100, risk_level is computed automatically. "
        "The device immediately appears in /devices, /network-map, and /overview."
    ),
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
    summary="Device detail",
    description="Returns full device info including computed open ports, protocol usage, and a plain-English security explanation.",
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
    )


@router.get(
    "/devices/{device_id}/explain",
    response_model=ExplainResponse,
    summary="Security explanation",
    description="Returns a plain-English explanation of why the device has its current risk level.",
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
    )


@router.get(
    "/network-map",
    response_model=NetworkMap,
    summary="Network topology map",
    description=(
        "Returns nodes (devices) and edges for rendering a network graph. "
        "All non-gateway devices connect to the primary gateway/router node."
    ),
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
    router  = next((d for d in devices if d["device_type"] == "router"), gateway)
    hub     = next((d for d in devices if d["device_type"] == "hub"), router)

    PARENT_MAP = {
        "gateway":    None,
        "router":     gateway["id"],
        "hub":        router["id"],
        "camera":     hub["id"],
        "sensor":     hub["id"],
        "smart_tv":   hub["id"],
        "laptop":     router["id"],
        "printer":    router["id"],
        "thermostat": hub["id"],
        "smartphone": router["id"],
    }

    edges = []
    for d in devices:
        parent_id = d.get("parent_id") or PARENT_MAP.get(d["device_type"], gateway["id"])
        if parent_id and parent_id != d["id"]:
            edges.append(NetworkEdge(source=parent_id, target=d["id"]))

    return NetworkMap(nodes=nodes, edges=edges)
