from pydantic import BaseModel
from datetime import datetime

class SmokeDetectionBase(BaseModel):
    location: str
    intensity: float
    is_alarm_triggered: bool

class SmokeDetectionCreate(SmokeDetectionBase):
    pass

class SmokeDetectionUpdate(SmokeDetectionBase):
    pass

class SmokeDetection(SmokeDetectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True