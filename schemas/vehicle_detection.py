from pydantic import BaseModel
from datetime import datetime

class VehicleDetectionBase(BaseModel):
    camera_id: str
    timestamp: datetime
    vehicle_type: str
    confidence: float
    bbox: str  # JSON string

class VehicleDetectionCreate(VehicleDetectionBase):
    pass

class VehicleDetection(VehicleDetectionBase):
    id: int

    class Config:
        orm_mode = True