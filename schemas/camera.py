from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CameraBase(BaseModel):
    camera_id: str
    rtsp_url: str
    status: bool = True
    property_id: Optional[str] = None
    zone_id: Optional[str] = None
    capabilities: Optional[str] = None  # JSON encoded as a string

class CameraCreate(CameraBase):
    pass

class Camera(CameraBase):
    id: int
    last_active: Optional[datetime] = None

    class Config:
        orm_mode = True