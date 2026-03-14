from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.models.telemetry import DeviceType


class EventCategory(str, Enum):
    SYSTEM = "SYSTEM"
    TELEMETRY = "TELEMETRY"
    DETECTION = "DETECTION"
    POLICY = "POLICY"
    TRUST = "TRUST"
    PROTECTION = "PROTECTION"
    ATTACK = "ATTACK"


class Event(BaseModel):
    event_id: str
    category: EventCategory
    event_type: str
    device_id: Optional[str] = None
    device_type: Optional[DeviceType] = None
    description: str
    metadata: dict = {}
    timestamp: datetime


class EventSummary(BaseModel):
    total_events: int
    by_category: dict[str, int]
    by_device: dict[str, int]
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None
