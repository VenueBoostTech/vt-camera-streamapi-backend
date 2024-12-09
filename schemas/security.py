from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.security import ThreatSeverity

class ThreatDetectionBase(BaseModel):
    type: str
    location: str
    severity: ThreatSeverity
    description: Optional[str] = None

class ThreatDetectionCreate(ThreatDetectionBase):
    pass

class ThreatDetectionUpdate(ThreatDetectionBase):
    pass

class ThreatDetection(ThreatDetectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SleepingDetectionBase(BaseModel):
    staff_id: int
    timestamp: datetime
    duration: float

class SleepingDetectionCreate(SleepingDetectionBase):
    pass

class SleepingDetectionUpdate(SleepingDetectionBase):
    pass

class SleepingDetection(SleepingDetectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True