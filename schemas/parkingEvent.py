from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum


class ParkingEventType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    VIOLATION = "VIOLATION"


class ParkingEventBase(BaseModel):
    vehicle_id: UUID
    zone_id: UUID
    type: ParkingEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parking_spot: Optional[str] = None
    duration: Optional[int] = None  # Duration in minutes
    metadata: Optional[Dict] = None  # Additional metadata


class ParkingEventCreate(ParkingEventBase):
    pass


class ParkingEventUpdate(BaseModel):
    parking_spot: Optional[str] = None
    duration: Optional[int] = None
    metadata: Optional[Dict] = None


class ParkingEvent(ParkingEventBase):
    id: UUID

    class Config:
        orm_mode = True
