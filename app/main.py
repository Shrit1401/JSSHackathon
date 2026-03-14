from __future__ import annotations

import asyncio
import logging
import random
import warnings
from contextlib import asynccontextmanager
from datetime import datetime, timezone

warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.supabase_client import supabase
from app.routers import alerts, devices, events, simulation, whatsapp
from app.services.trust_engine import SEED_DEVICES, compute_risk_level
from app.services.ml_pipeline import pipeline
from app.services.whatsapp_alerts import send_compromise_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("iot_monitor")


async def seed_devices_if_empty() -> None:
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").select("id").limit(1).execute()
        )
        if result.data:
            logger.info("Devices table already seeded (%d+ rows found).", len(result.data))
            return

        logger.info("Devices table empty — seeding %d devices…", len(SEED_DEVICES))
        now = datetime.now(timezone.utc).isoformat()
        rows = [{**d, "last_seen": now, "created_at": now} for d in SEED_DEVICES]
        await asyncio.to_thread(
            lambda: supabase.table("devices").insert(rows).execute()
        )
        logger.info("Seed complete.")
    except Exception:
        logger.exception("seed_devices_if_empty failed — continuing without seed")


async def initialize_ml_pipeline() -> None:
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("devices").select("*").execute()
        )
        devices_list = result.data or []
        if not devices_list:
            logger.warning("No devices found — ML pipeline cannot initialize")
            return

        await asyncio.to_thread(lambda: pipeline.initialize(devices_list))
        logger.info("ML pipeline ready — %d devices mapped", len(pipeline.device_map))
    except Exception:
        logger.exception("ML pipeline initialization failed — falling back to simple mode")


async def _send_compromise_whatsapp(supa_id: str, trust: int, risk: str) -> None:
    try:
        dev_result = await asyncio.to_thread(
            lambda did=supa_id: supabase.table("devices")
            .select("name,device_type")
            .eq("id", did)
            .limit(1)
            .execute()
        )
        dev_row = dev_result.data[0] if dev_result.data else {}
        await asyncio.to_thread(
            lambda: send_compromise_alert(
                device_name=dev_row.get("name", "Unknown"),
                device_id=supa_id,
                device_type=dev_row.get("device_type", "unknown"),
                trust_score=trust,
                risk_level=risk,
            )
        )
    except Exception:
        logger.exception("background — WhatsApp send failed for %s", supa_id)


async def _update_device_trust(supa_id: str, trust: int, risk: str, now: str) -> tuple[str, int, str] | None:
    try:
        await asyncio.to_thread(
            lambda sid=supa_id, t=trust, r=risk: supabase.table("devices")
            .update({"trust_score": t, "risk_level": r, "last_seen": now})
            .eq("id", sid)
            .execute()
        )
        if risk == "COMPROMISED":
            return (supa_id, trust, risk)
    except Exception:
        logger.exception("Failed to sync trust for device %s", supa_id)
    return None


async def run_simulation_tick() -> None:
    if not pipeline.is_trained:
        return

    try:
        tick_results = await asyncio.to_thread(pipeline.run_tick)
    except Exception:
        logger.exception("ML pipeline tick failed")
        return

    if not tick_results:
        return

    now = datetime.now(timezone.utc).isoformat()

    update_coros = [
        _update_device_trust(sid, data["trust_score"], data["risk_level"], now)
        for sid, data in tick_results.items()
    ]
    results = await asyncio.gather(*update_coros)

    for r in results:
        if r is not None:
            asyncio.create_task(_send_compromise_whatsapp(*r))

    try:
        new_alerts = await asyncio.to_thread(pipeline.get_new_alerts)
        if new_alerts:
            name_cache: dict[str, str] = {}
            unique_ids = {a["device_id"] for a in new_alerts[:10]}
            name_coros = []
            for did in unique_ids:
                async def _fetch_name(d=did):
                    try:
                        res = await asyncio.to_thread(
                            lambda dd=d: supabase.table("devices")
                            .select("name").eq("id", dd).limit(1).execute()
                        )
                        name_cache[d] = res.data[0].get("name", "") if res.data else ""
                    except Exception:
                        name_cache[d] = ""
                name_coros.append(_fetch_name())
            await asyncio.gather(*name_coros)

            alert_rows = []
            for alert_data in new_alerts[:10]:
                alert_rows.append({
                    "device_id": alert_data["device_id"],
                    "device_name": name_cache.get(alert_data["device_id"], ""),
                    "alert_type": alert_data["alert_type"],
                    "severity": alert_data["severity"],
                    "message": alert_data["message"],
                    "timestamp": alert_data["timestamp"],
                })
            if alert_rows:
                await asyncio.to_thread(
                    lambda rows=alert_rows: supabase.table("alerts").insert(rows).execute()
                )
    except Exception:
        logger.exception("Failed to sync ML alerts to Supabase")


async def simulation_loop() -> None:
    logger.info("ML-driven simulation loop started.")
    while True:
        sleep_secs = random.uniform(5, 10)
        await asyncio.sleep(sleep_secs)
        try:
            await run_simulation_tick()
        except Exception:
            logger.exception("simulation_loop tick failed — continuing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("━━━ IoT Trust Monitor starting up ━━━")
    await seed_devices_if_empty()
    await initialize_ml_pipeline()
    task = asyncio.create_task(simulation_loop())
    yield
    logger.info("━━━ IoT Trust Monitor shutting down ━━━")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="IoT Trust Monitor",
    description=(
        "Real-time IoT security monitoring backend powered by ML.\n\n"
        "Uses Isolation Forest anomaly detection, behavioral drift analysis, "
        "policy evaluation, and multi-signal trust fusion to monitor network "
        "devices, calculate trust scores, detect suspicious behaviour, and "
        "generate alerts."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
    )


app.include_router(devices.router, tags=["Devices"])
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(events.router, tags=["Events"])
app.include_router(simulation.router, tags=["Simulation"])
app.include_router(whatsapp.router, tags=["WhatsApp"])


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "ml_pipeline": pipeline.is_trained,
        "devices_mapped": len(pipeline.device_map),
        "active_attacks": len(pipeline.active_attacks),
    }
