from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import SimulateAttackRequest, SimulateAttackResponse
from app.services.trust_engine import (
    build_alert_payload,
    compute_risk_level,
    should_create_alert,
)
from app.services.ml_pipeline import pipeline
from app.services.whatsapp_alerts import send_attack_evidence_card

logger = logging.getLogger("iot_monitor.simulation")
router = APIRouter()

ATTACK_TYPES = [
    "TRAFFIC_SPIKE", "POLICY_VIOLATION", "NEW_DESTINATION",
    "BACKDOOR", "DATA_EXFILTRATION",
]

BACKDOOR_PRESETS = {
    "low":    {"cycles": 2, "traffic_low": 0.5,  "traffic_high": 2.0},
    "medium": {"cycles": 3, "traffic_low": 3.0,  "traffic_high": 8.0},
    "high":   {"cycles": 5, "traffic_low": 10.0, "traffic_high": 20.0},
}


async def _post_attack_background(
    device: dict,
    device_id: str,
    attack_type: str,
    old_trust: int,
    new_trust: int,
    old_risk: str,
    new_risk: str,
) -> None:
    try:
        ml_alerts = await asyncio.to_thread(pipeline.get_new_alerts)
        matching = [
            {
                "device_id": device_id,
                "device_name": device["name"],
                "alert_type": a["alert_type"],
                "severity": a["severity"],
                "message": a["message"],
                "timestamp": a["timestamp"],
            }
            for a in ml_alerts[:5]
            if a["device_id"] == device_id
        ]
        if matching:
            await asyncio.to_thread(
                lambda rows=matching: supabase.table("alerts").insert(rows).execute()
            )
    except Exception:
        logger.exception("background — ML alert insert failed for %s", device_id)

    breakdown_info = ""
    detail = pipeline.get_device_trust_detail(device_id)
    if detail:
        breakdown_info = (
            f" ML anomaly={detail['ml_anomaly_score']:.2f},"
            f" drift={detail['drift_score']:.2f},"
            f" policy_violations={detail['policy_violations_total']},"
            f" total_penalty={detail['total_penalty']:.1f}"
        )
    logger.info(
        "ml-attack  device=%-20s  type=%-20s  trust=%d→%d  risk=%s→%s%s",
        device["name"], attack_type, old_trust, new_trust,
        old_risk, new_risk, breakdown_info,
    )

    if new_risk == "COMPROMISED":
        try:
            await asyncio.to_thread(
                lambda: send_attack_evidence_card(
                    device=device,
                    attack_type=attack_type,
                    old_trust=old_trust,
                    new_trust=new_trust,
                    old_risk=old_risk,
                    new_risk=new_risk,
                )
            )
        except Exception:
            logger.exception("background — WhatsApp send failed for %s", device["name"])


async def _run_ml_attack(
    device_id: str,
    attack_type: str,
    cycles: int,
    traffic_delta_low: float,
    traffic_delta_high: float,
    new_status: str,
    event_description: str,
    status_detail: str,
    detection_difficulty: int | None = None,
) -> SimulateAttackResponse:
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices")
            .select("*")
            .eq("id", device_id)
            .execute()
        )
    except Exception as exc:
        logger.exception("attack simulation — DB fetch error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    device = rows[0]

    old_trust = device["trust_score"]
    old_risk = device["risk_level"]

    ml_result = await asyncio.to_thread(
        lambda: pipeline.run_attack_cycles(device_id, attack_type, cycles=cycles)
    )

    if ml_result:
        new_trust = ml_result["trust_score"]
        new_risk = ml_result["risk_level"]
    else:
        from app.services.trust_engine import apply_attack_penalty
        new_trust = apply_attack_penalty(old_trust)
        new_risk = compute_risk_level(new_trust)

    new_traffic = round(device["traffic_rate"] + random.uniform(traffic_delta_low, traffic_delta_high), 2)
    now = datetime.now(timezone.utc).isoformat()

    try:
        device_update = asyncio.to_thread(
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
        event_insert = asyncio.to_thread(
            lambda: supabase.table("events")
            .insert({
                "device_id": device_id,
                "event_type": attack_type,
                "description": f"[ML] {event_description}",
                "timestamp": now,
            })
            .execute()
        )
        alert_payload = build_alert_payload(device, attack_type, new_trust)
        alert_insert = asyncio.to_thread(
            lambda p=alert_payload: supabase.table("alerts").insert(p).execute()
        )
        results = await asyncio.gather(
            device_update, event_insert, alert_insert,
            return_exceptions=True,
        )
        if isinstance(results[0], Exception) or isinstance(results[1], Exception):
            raise HTTPException(status_code=502, detail="Database error")
        alert_created = not isinstance(results[2], Exception)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("attack simulation — DB write error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    response = SimulateAttackResponse(
        device_id=device_id,
        attack_type=attack_type,
        old_trust_score=old_trust,
        new_trust_score=new_trust,
        old_risk_level=old_risk,
        new_risk_level=new_risk,
        alert_created=alert_created,
        message=(
            f"{attack_type} simulated on '{device['name']}' via ML pipeline. "
            f"Trust dropped {old_trust} → {new_trust}. "
            f"Risk: {old_risk} → {new_risk}. {status_detail}"
        ),
        detection_difficulty=detection_difficulty,
    )

    asyncio.create_task(_post_attack_background(
        device=device,
        device_id=device_id,
        attack_type=attack_type,
        old_trust=old_trust,
        new_trust=new_trust,
        old_risk=old_risk,
        new_risk=new_risk,
    ))

    return response


@router.post(
    "/simulate-attack",
    response_model=SimulateAttackResponse,
    summary="Trigger an ML-driven attack simulation",
    description=(
        "Simulates a cyberattack on a device using the full ML pipeline. "
        "Generates attack telemetry, runs IsolationForest anomaly detection, "
        "drift analysis, policy checking, and multi-signal trust fusion. "
        "Trust scores reflect real ML computation, not random penalties."
    ),
)
async def simulate_attack(body: SimulateAttackRequest):
    attack_type = body.attack_type
    if attack_type is not None and attack_type not in ATTACK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid attack_type '{attack_type}'. Must be one of: {ATTACK_TYPES}",
        )
    if attack_type is None:
        attack_type = random.choice(ATTACK_TYPES)

    return await _run_ml_attack(
        device_id=body.device_id,
        attack_type=attack_type,
        cycles=3,
        traffic_delta_low=5.0,
        traffic_delta_high=15.0,
        new_status="online",
        event_description=f"{attack_type} attack detected by ML pipeline",
        status_detail="Trust score computed by IsolationForest + drift + policy analysis.",
    )


@router.post(
    "/simulate/backdoor",
    response_model=SimulateAttackResponse,
    summary="Simulate a backdoor implant (ML-driven)",
    description=(
        "Implants a backdoor on the device. The ML pipeline generates "
        "SSH/Telnet traffic to unknown external IPs, triggering anomaly "
        "detection, policy violations, and behavioral drift."
    ),
)
async def simulate_backdoor(body: SimulateAttackRequest):
    preset = BACKDOOR_PRESETS[body.stealth_level or "medium"]
    detection = {"low": 85, "medium": 50, "high": 20}[body.stealth_level or "medium"]
    return await _run_ml_attack(
        device_id=body.device_id,
        attack_type="BACKDOOR",
        cycles=preset["cycles"],
        traffic_delta_low=preset["traffic_low"],
        traffic_delta_high=preset["traffic_high"],
        new_status="compromised",
        event_description="Backdoor implant — persistent remote access via SSH to unknown external",
        status_detail="Device status set to 'compromised'.",
        detection_difficulty=detection,
    )


@router.post(
    "/simulate/traffic-spike",
    response_model=SimulateAttackResponse,
    summary="Simulate a traffic flood / DDoS (ML-driven)",
    description=(
        "Floods the device with massive traffic. The ML pipeline detects "
        "the anomalous packet rates and traffic volume through IsolationForest."
    ),
)
async def simulate_traffic_spike(body: SimulateAttackRequest):
    return await _run_ml_attack(
        device_id=body.device_id,
        attack_type="TRAFFIC_SPIKE",
        cycles=3,
        traffic_delta_low=15.0,
        traffic_delta_high=40.0,
        new_status="online",
        event_description="Abnormal outbound traffic flood detected by ML — possible DDoS or botnet",
        status_detail="Traffic flooded.",
    )


@router.post(
    "/simulate/data-exfiltration",
    response_model=SimulateAttackResponse,
    summary="Simulate data exfiltration (ML-driven)",
    description=(
        "Initiates a sustained outbound data stream. The ML pipeline "
        "detects anomalous bytes_sent patterns and external connection ratios."
    ),
)
async def simulate_data_exfiltration(body: SimulateAttackRequest):
    return await _run_ml_attack(
        device_id=body.device_id,
        attack_type="DATA_EXFILTRATION",
        cycles=4,
        traffic_delta_low=10.0,
        traffic_delta_high=25.0,
        new_status="online",
        event_description="Sustained data exfiltration detected by ML — anomalous outbound volume",
        status_detail="Sustained exfiltration traffic detected.",
    )


@router.post("/reset-network", summary="Reset all devices to healthy state")
async def reset_network():
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").select("id").execute()
        )
    except Exception as exc:
        logger.exception("POST /reset-network — DB fetch error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    await asyncio.to_thread(pipeline.stop_all_attacks)

    device_ids = [row["id"] for row in (result.data or [])]
    now = datetime.now(timezone.utc).isoformat()

    async def _reset_one(did: str) -> bool:
        try:
            t = random.randint(85, 95)
            await asyncio.to_thread(
                lambda d=did, tr=t: supabase.table("devices").update({
                    "trust_score": tr,
                    "risk_level": "SAFE",
                    "traffic_rate": round(random.uniform(0.1, 1.5), 2),
                    "status": "online",
                    "last_seen": now,
                }).eq("id", d).execute()
            )
            return True
        except Exception:
            logger.exception("POST /reset-network — failed to reset device %s", did)
            return False

    results = await asyncio.gather(*[_reset_one(did) for did in device_ids])
    updated = sum(results)

    try:
        await asyncio.to_thread(
            lambda: supabase.table("alerts").delete().neq("id", "").execute()
        )
        await asyncio.to_thread(
            lambda: supabase.table("events").delete().neq("id", "").execute()
        )
    except Exception:
        logger.exception("POST /reset-network — failed to clear alerts/events")

    try:
        all_devices = await asyncio.to_thread(
            lambda: supabase.table("devices").select("*").execute()
        )
        await asyncio.to_thread(lambda: pipeline.reset())
        await asyncio.to_thread(lambda: pipeline.initialize(all_devices.data or []))
    except Exception:
        logger.exception("POST /reset-network — ML pipeline re-init failed")

    logger.info("reset-network  reset %d devices, ML pipeline re-initialized", updated)
    return {"message": f"Reset {updated} devices to healthy state. ML pipeline re-trained.", "devices_reset": updated}
