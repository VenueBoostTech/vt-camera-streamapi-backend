from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
from typing import Optional

class EntryLogBase(BaseModel):
    camera_id: Optional[str] = None  # Optional to match nullable=True in SQLAlchemy
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))  # Default to current UTC
    person_id: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    entering: Optional[int] = 0  # Default value of 0
    exiting: Optional[int] = 0
    in_store: Optional[int] = 0

class EntryLogSummary(BaseModel):
    time: str  # Time in 'HH:MM' format
    entering: int
    exiting: int
    inStore: int


class EntryLogCreate(EntryLogBase):
    pass

class EntryLog(EntryLogBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # UUID for unique ID

    class Config:
        orm_mode = True
