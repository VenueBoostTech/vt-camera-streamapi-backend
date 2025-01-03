from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CameraBase(BaseModel):
    camera_id: str
    rtsp_url: Optional[str] = None
    status: str = "ACTIVE"  # Default to "ACTIVE" as per the SQLAlchemy model
    property_id: str
    zone_id: str
    capabilities: Optional[List[str]] = None  # JSON encoded as a string
    name: str
    location: Optional[str] = None
    direction: Optional[str] = None
    coverage_area: Optional[dict] = None  # JSON field for the coverage area
    store_id: Optional[str] = None

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: str
    last_active: Optional[datetime] = None

    class Config:
        orm_mode = True

class CameraStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"

class CameraTypeEnum(str, Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    THERMAL = "THERMAL"
