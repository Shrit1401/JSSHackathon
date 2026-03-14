from __future__ import annotations

import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import EventOut

logger = logging.getLogger("iot_monitor.events")
router = APIRouter()


@router.get(
    "/events",
    response_model=List[EventOut],
    summary="Recent events",
    description="Returns the 100 most recent device events (including background simulation events), newest first.",
)
async def list_events():
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("events")
            .select("*")
            .order("timestamp", desc=True)
            .limit(100)
            .execute()
        )
    except Exception as exc:
        logger.exception("GET /events — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    return [EventOut(**e) for e in (result.data or [])]
