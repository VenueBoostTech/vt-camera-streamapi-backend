from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PACKAGE_THEFT = "PACKAGE_THEFT"
    SMOKE_DETECTED = "SMOKE_DETECTED"
    SUSPICIOUS_BEHAVIOR = "SUSPICIOUS_BEHAVIOR"


class EventSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(str, Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class SecurityEventBase(BaseModel):
    property_id: UUID
    zone_id: UUID
    type: EventType
    severity: EventSeverity
    status: EventStatus = EventStatus.NEW
    timestamp: datetime
    evidence: Optional[List[Dict]]  # List of serialized Detection objects or IDs
    meta_data: Optional[Dict]  # Additional metadata as JSON


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEvent(SecurityEventBase):
    id: UUID

    class Config:
        orm_mode = True
