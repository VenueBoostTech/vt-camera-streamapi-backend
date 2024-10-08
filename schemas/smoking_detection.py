from pydantic import BaseModel
from datetime import datetime

class SmokingDetectionBase(BaseModel):
    camera_id: str
    timestamp: datetime
    confidence: float
    bbox: str  # JSON string

class SmokingDetectionCreate(SmokingDetectionBase):
    pass

class SmokingDetection(SmokingDetectionBase):
    id: int

    class Config:
        orm_mode = True