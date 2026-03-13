import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import SimulateAttackRequest, SimulateAttackResponse
from app.services.trust_engine import (
    adjust_trust_score,
    apply_attack_penalty,
    build_alert_payload,
    compute_risk_level,
    should_create_alert,
)

logger = logging.getLogger("iot_monitor.simulation")
router = APIRouter()

ATTACK_TYPES = ["TRAFFIC_SPIKE", "POLICY_VIOLATION", "NEW_DESTINATION", "BACKDOOR", "DATA_EXFILTRATION"]

BACKDOOR_PRESETS = {
    "low":    {"trust_low": -10, "trust_high": -5,  "traffic_low": 0.5, "traffic_high": 2.0,  "detection": 85},
    "medium": {"trust_low": -25, "trust_high": -15, "traffic_low": 3.0, "traffic_high": 8.0,  "detection": 50},
    "high":   {"trust_low": -45, "trust_high": -30, "traffic_low": 10.0, "traffic_high": 20.0, "detection": 20},
}


@router.post(
    "/simulate-attack",
    response_model=SimulateAttackResponse,
    summary="Manually trigger an attack simulation",
    description=(
        "Simulates a cyberattack on a specific device. "
        "Drops its trust score, updates risk level, inserts an event, "
        "and creates an alert if warranted. "
        "`attack_type` is optional — a random type is chosen if omitted."
    ),
)
async def simulate_attack(body: SimulateAttackRequest):
    # ── fetch device ──────────────────────────────────────────────────────────
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices")
            .select("*")
            .eq("id", body.device_id)
            .execute()
        )
    except Exception as exc:
        logger.exception("POST /simulate-attack — DB fetch error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Device '{body.device_id}' not found")
    device = rows[0]

    # ── validate attack_type if provided ─────────────────────────────────────
    attack_type = body.attack_type
    if attack_type is not None and attack_type not in ATTACK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid attack_type '{attack_type}'. Must be one of: {ATTACK_TYPES}",
        )
    if attack_type is None:
        attack_type = random.choice(ATTACK_TYPES)

    # ── compute new state ─────────────────────────────────────────────────────
    old_trust = device["trust_score"]
    old_risk = device["risk_level"]
    new_trust = apply_attack_penalty(old_trust)
    new_risk = compute_risk_level(new_trust)
    new_traffic = round(device["traffic_rate"] + random.uniform(5.0, 15.0), 2)
    now = datetime.now(timezone.utc).isoformat()

    # ── persist ───────────────────────────────────────────────────────────────
    try:
        await asyncio.to_thread(
            lambda: supabase.table("devices")
            .update({
                "trust_score": new_trust,
                "risk_level": new_risk,
                "traffic_rate": new_traffic,
                "last_seen": now,
            })
            .eq("id", body.device_id)
            .execute()
        )

        await asyncio.to_thread(
            lambda: supabase.table("events")
            .insert({
                "device_id": body.device_id,
                "event_type": attack_type,
                "description": f"[Manual] {attack_type} simulated on {device['name']}",
                "timestamp": now,
            })
            .execute()
        )
    except Exception as exc:
        logger.exception("POST /simulate-attack — DB write error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    # ── alert (best-effort — don't fail the request if this errors) ───────────
    alert_created = should_create_alert(attack_type, new_trust, old_trust)
    if alert_created:
        try:
            payload = build_alert_payload(device, attack_type, new_trust)
            await asyncio.to_thread(
                lambda: supabase.table("alerts").insert(payload).execute()
            )
        except Exception:
            logger.exception("POST /simulate-attack — alert insert failed (non-fatal)")
            alert_created = False

    logger.info(
        "simulate-attack  device=%-20s  type=%-20s  trust=%d→%d  risk=%s→%s  alert=%s",
        device["name"], attack_type, old_trust, new_trust, old_risk, new_risk, alert_created,
    )

    return SimulateAttackResponse(
        device_id=body.device_id,
        attack_type=attack_type,
        old_trust_score=old_trust,
        new_trust_score=new_trust,
        old_risk_level=old_risk,
        new_risk_level=new_risk,
        alert_created=alert_created,
        message=(
            f"{attack_type} simulated on '{device['name']}'. "
            f"Trust dropped {old_trust} → {new_trust}. "
            f"Risk: {old_risk} → {new_risk}."
        ),
    )


# ---------------------------------------------------------------------------
# Helper shared by the three dedicated attack endpoints
# ---------------------------------------------------------------------------

async def _run_dedicated_attack(
    device_id: str,
    attack_type: str,
    traffic_delta_low: float,
    traffic_delta_high: float,
    new_status: str,
    event_description: str,
    status_detail: str,
    trust_delta_low: Optional[int] = None,
    trust_delta_high: Optional[int] = None,
    detection_difficulty: Optional[int] = None,
) -> SimulateAttackResponse:
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices")
            .select("*")
            .eq("id", device_id)
            .execute()
        )
    except Exception as exc:
        logger.exception("dedicated attack — DB fetch error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    device = rows[0]

    old_trust = device["trust_score"]
    old_risk = device["risk_level"]
    if trust_delta_low is not None and trust_delta_high is not None:
        delta = random.randint(trust_delta_low, trust_delta_high)
        new_trust = max(0, old_trust + delta)
    else:
        new_trust = adjust_trust_score(old_trust, attack_type)
    new_risk = compute_risk_level(new_trust)
    new_traffic = round(device["traffic_rate"] + random.uniform(traffic_delta_low, traffic_delta_high), 2)
    now = datetime.now(timezone.utc).isoformat()

    try:
        await asyncio.to_thread(
            lambda: supabase.table("devices")
            .update({
                "trust_score": new_trust,
                "risk_level": new_risk,
                "traffic_rate": new_traffic,
                "status": new_status,
                "last_seen": now,
            })
            .eq("id", device_id)
            .execute()
        )

        await asyncio.to_thread(
            lambda: supabase.table("events")
            .insert({
                "device_id": device_id,
                "event_type": attack_type,
                "description": f"[Manual] {event_description}",
                "timestamp": now,
            })
            .execute()
        )
    except Exception as exc:
        logger.exception("dedicated attack — DB write error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    # Always insert alert for dedicated attack endpoints
    alert_created = True
    try:
        payload = build_alert_payload(device, attack_type, new_trust)
        await asyncio.to_thread(
            lambda: supabase.table("alerts").insert(payload).execute()
        )
    except Exception:
        logger.exception("dedicated attack — alert insert failed (non-fatal)")
        alert_created = False

    logger.info(
        "dedicated-attack  device=%-20s  type=%-20s  trust=%d→%d  risk=%s→%s  status=%s  alert=%s",
        device["name"], attack_type, old_trust, new_trust, old_risk, new_risk, new_status, alert_created,
    )

    return SimulateAttackResponse(
        device_id=device_id,
        attack_type=attack_type,
        old_trust_score=old_trust,
        new_trust_score=new_trust,
        old_risk_level=old_risk,
        new_risk_level=new_risk,
        alert_created=alert_created,
        message=(
            f"{attack_type} simulated on '{device['name']}'. "
            f"Trust dropped {old_trust} → {new_trust}. "
            f"Risk: {old_risk} → {new_risk}. {status_detail}"
        ),
        detection_difficulty=detection_difficulty,
    )


# ---------------------------------------------------------------------------
# Dedicated attack endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/simulate/backdoor",
    response_model=SimulateAttackResponse,
    summary="Simulate a backdoor implant attack",
    description=(
        "Implants a silent persistent backdoor on the device. "
        "Trust drops 25–40, traffic increases only 2–8 MB/s (stealthy), "
        "device status set to 'compromised', CRITICAL alert created."
    ),
)
async def simulate_backdoor(body: SimulateAttackRequest):
    preset = BACKDOOR_PRESETS[body.stealth_level or "medium"]
    return await _run_dedicated_attack(
        device_id=body.device_id,
        attack_type="BACKDOOR",
        traffic_delta_low=preset["traffic_low"],
        traffic_delta_high=preset["traffic_high"],
        new_status="compromised",
        event_description="Backdoor implant detected — persistent remote access established",
        status_detail="Device status set to 'compromised'.",
        trust_delta_low=preset["trust_low"],
        trust_delta_high=preset["trust_high"],
        detection_difficulty=preset["detection"],
    )


@router.post(
    "/simulate/traffic-spike",
    response_model=SimulateAttackResponse,
    summary="Simulate a traffic flood / DDoS attack",
    description=(
        "Floods the device with a massive traffic surge. "
        "Trust drops 10–20, traffic increases 15–40 MB/s, HIGH alert created."
    ),
)
async def simulate_traffic_spike(body: SimulateAttackRequest):
    return await _run_dedicated_attack(
        device_id=body.device_id,
        attack_type="TRAFFIC_SPIKE",
        traffic_delta_low=15.0,
        traffic_delta_high=40.0,
        new_status="online",
        event_description="Abnormal outbound traffic flood — possible DDoS or botnet activity",
        status_detail="Traffic flooded.",
    )


@router.post(
    "/simulate/data-exfiltration",
    response_model=SimulateAttackResponse,
    summary="Simulate a data exfiltration attack",
    description=(
        "Initiates a sustained outbound data stream from the device. "
        "Trust drops 15–25, traffic increases 10–25 MB/s (sustained), HIGH alert created."
    ),
)
async def simulate_data_exfiltration(body: SimulateAttackRequest):
    return await _run_dedicated_attack(
        device_id=body.device_id,
        attack_type="DATA_EXFILTRATION",
        traffic_delta_low=10.0,
        traffic_delta_high=25.0,
        new_status="online",
        event_description="Sustained data exfiltration stream detected — sensitive data may be leaving network",
        status_detail="Sustained exfiltration traffic detected.",
    )


# ---------------------------------------------------------------------------
# Network reset
# ---------------------------------------------------------------------------

@router.post("/reset-network", summary="Reset all devices to healthy state")
async def reset_network():
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").select("id").execute()
        )
    except Exception as exc:
        logger.exception("POST /reset-network — DB fetch error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    device_ids = [row["id"] for row in (result.data or [])]
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    for device_id in device_ids:
        new_trust = random.randint(85, 95)
        try:
            await asyncio.to_thread(
                lambda did=device_id, t=new_trust: supabase.table("devices").update({
                    "trust_score": t,
                    "risk_level": "SAFE",
                    "status": "online",
                    "last_seen": now,
                }).eq("id", did).execute()
            )
            updated += 1
        except Exception:
            logger.exception("POST /reset-network — failed to reset device %s", device_id)

    logger.info("reset-network  reset %d devices to healthy state", updated)
    return {"message": f"Reset {updated} devices to healthy state.", "devices_reset": updated}
