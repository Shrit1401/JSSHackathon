from __future__ import annotations

import asyncio
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.database.supabase_client import supabase
from app.models.device_models import AlertOut
from app.services.ml_pipeline import pipeline

logger = logging.getLogger("iot_monitor.alerts")
router = APIRouter()


@router.get(
    "/alerts",
    response_model=List[AlertOut],
    summary="Recent alerts (DB + ML)",
    description=(
        "Returns the 50 most recent security alerts across all devices. "
        "Includes both manually-triggered alerts and ML-generated alerts "
        "from IsolationForest anomaly detection, drift analysis, and policy evaluation."
    ),
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


@router.get(
    "/alerts/ml-summary",
    summary="ML alert engine summary",
    description="Returns aggregate stats from the ML alert engine — counts by type, severity, and device.",
)
async def ml_alert_summary():
    if not pipeline.is_trained:
        return {"error": "ML pipeline not initialized"}

    try:
        summary = pipeline.alert_manager.get_summary()
        return {
            "total_alerts": summary.total_alerts,
            "by_type": summary.by_type,
            "by_severity": summary.by_severity,
            "by_device": {
                pipeline.reverse_map.get(did, did): count
                for did, count in summary.by_device.items()
            },
            "unacknowledged": summary.unacknowledged,
        }
    except Exception as exc:
        logger.exception("GET /alerts/ml-summary — error")
        raise HTTPException(status_code=500, detail="ML alert summary failed") from exc
