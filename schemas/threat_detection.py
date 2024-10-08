from pydantic import BaseModel
from datetime import datetime

class ThreatDetectionBase(BaseModel):
    camera_id: str
    timestamp: datetime
    threat_type: str
    confidence: float
    bbox: str  # JSON string

class ThreatDetectionCreate(ThreatDetectionBase):
    pass

class ThreatDetection(ThreatDetectionBase):
    id: int

    class Config:
        orm_mode = True