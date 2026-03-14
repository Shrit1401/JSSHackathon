from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.events import Event, EventCategory, EventSummary
from app.services.event_timeline import EventTimeline
from app.api.telemetry_routes import generator
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.trust_routes import trust_engine

router = APIRouter(prefix="/events", tags=["Event Timeline"])

timeline = EventTimeline(generator, drift_detector, policy_engine, ml_detector, trust_engine)


@router.get("")
def get_events(
    category: Optional[EventCategory] = None,
    device_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=100, le=500),
) -> list[Event]:
    return timeline.get_timeline(category, device_id, event_type, limit)


@router.get("/device/{device_id}")
def get_device_events(device_id: str, limit: int = Query(default=100, le=500)) -> list[Event]:
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return timeline.get_device_timeline(device_id, limit)


@router.get("/attacks")
def get_attack_events(limit: int = Query(default=50, le=200)) -> list[Event]:
    return timeline.get_timeline(category=EventCategory.ATTACK, limit=limit)


@router.get("/detections")
def get_detection_events(limit: int = Query(default=50, le=200)) -> list[Event]:
    return timeline.get_timeline(category=EventCategory.DETECTION, limit=limit)


@router.get("/summary")
def get_event_summary() -> EventSummary:
    return timeline.get_summary()
