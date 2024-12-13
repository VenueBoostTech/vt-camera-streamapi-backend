from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class IncidentBase(BaseModel):
    property_id: UUID
    related_events: Optional[List[UUID]]  # List of related SecurityEvent IDs
    status: str  # Example: "NEW", "CLOSED"
    priority: int
    created_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    @field_validator("related_events")
    def convert_uuids_to_strings(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    status: Optional[str]
    priority: Optional[int]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]


class Incident(IncidentBase):
    id: UUID

    class Config:
        orm_mode = True