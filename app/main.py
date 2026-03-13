import asyncio
import logging
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.supabase_client import supabase
from app.routers import alerts, devices, events, simulation
from app.services.trust_engine import (
    SEED_DEVICES,
    compute_risk_level,
    recover_trust_score,
)

  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("iot_monitor")


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Background simulation
# ---------------------------------------------------------------------------

async def run_simulation_tick() -> None:
    result = await asyncio.to_thread(
        lambda: supabase.table("devices").select("*").execute()
    )
    devices_list = result.data or []
    if not devices_list:
        logger.warning("simulation_tick: no devices in DB, skipping")
        return

    device = random.choice(devices_list)
    old_trust = device["trust_score"]
    now = datetime.now(timezone.utc).isoformat()

    roll = random.random()
    if roll < 0.85:
        # Normal: small traffic fluctuation + gentle trust recovery
        new_trust = recover_trust_score(old_trust)
        new_traffic = max(0.0, round(device["traffic_rate"] + random.uniform(-2.0, 2.0), 2))
        await asyncio.to_thread(
            lambda: supabase.table("devices")
            .update({
                "trust_score": new_trust,
                "risk_level": compute_risk_level(new_trust),
                "traffic_rate": new_traffic,
                "last_seen": now,
            })
            .eq("id", device["id"])
            .execute()
        )
        logger.debug(
            "tick   device=%-20s  trust=%d→%d  (normal)",
            device["name"], old_trust, new_trust,
        )
    else:
        # Minor anomaly: small trust dip, no alert
        delta = random.randint(-5, -1)
        new_trust = max(0, min(100, old_trust + delta))
        new_traffic = max(0.0, round(device["traffic_rate"] + random.uniform(-1.0, 3.0), 2))
        await asyncio.to_thread(
            lambda: supabase.table("devices")
            .update({
                "trust_score": new_trust,
                "risk_level": compute_risk_level(new_trust),
                "traffic_rate": new_traffic,
                "last_seen": now,
            })
            .eq("id", device["id"])
            .execute()
        )
        await asyncio.to_thread(
            lambda: supabase.table("events")
            .insert({
                "device_id": device["id"],
                "event_type": "TRAFFIC_FLUCTUATION",
                "description": f"[Auto] Minor traffic fluctuation on {device['name']}",
                "timestamp": now,
            })
            .execute()
        )
        logger.debug(
            "tick   device=%-20s  trust=%d→%d  (minor anomaly)",
            device["name"], old_trust, new_trust,
        )


async def simulation_loop() -> None:
    logger.info("Simulation loop started.")
    while True:
        sleep_secs = random.uniform(5, 10)
        await asyncio.sleep(sleep_secs)
        try:
            await run_simulation_tick()
        except Exception:
            logger.exception("simulation_loop tick failed — continuing")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("━━━ IoT Trust Monitor starting up ━━━")
    await seed_devices_if_empty()
    task = asyncio.create_task(simulation_loop())
    yield
    logger.info("━━━ IoT Trust Monitor shutting down ━━━")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IoT Trust Monitor",
    description=(
        "Real-time IoT security monitoring backend.\n\n"
        "Monitors network devices, calculates trust scores, detects suspicious "
        "behaviour, generates alerts, and runs a background simulation engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
       allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler — never leak a 500 stack trace to the client
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(devices.router, tags=["Devices"])
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(events.router, tags=["Events"])
app.include_router(simulation.router, tags=["Simulation"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
