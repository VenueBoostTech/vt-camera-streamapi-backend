from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class PatternType(str, Enum):
    RECURRING = "RECURRING"
    ANOMALY = "ANOMALY"
    SUSPICIOUS = "SUSPICIOUS"

class BehaviorBase(BaseModel):
    property_id: Optional[str]
    zone_id: Optional[str]
    pattern_type: PatternType
    activity_type: str
    frequency: int
    confidence: float
    last_detected: datetime

class BehaviorCreate(BehaviorBase):
    pass

class Behavior(BehaviorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
