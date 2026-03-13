import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import AlertOut

logger = logging.getLogger("iot_monitor.alerts")
router = APIRouter()


@router.get(
    "/alerts",
    response_model=List[AlertOut],
    summary="Recent alerts",
    description="Returns the 50 most recent security alerts across all devices, newest first.",
)
async def list_alerts():
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("alerts")
            .select("*")
            .order("timestamp", desc=True)
            .limit(50)
            .execute()
        )
    except Exception as exc:
        logger.exception("GET /alerts — DB error")
        raise HTTPException(status_code=502, detail="Database error") from exc

    return [AlertOut(**a) for a in (result.data or [])]
