from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class DetectionBase(BaseModel):
    camera_id: UUID
    timestamp: datetime
    type: str
    bbox: Optional[BoundingBox]  # Optional bounding box
    confidence: float
    tracking_id: Optional[str]
    attributes: Optional[Dict]  # Additional attributes as JSON


class DetectionCreate(DetectionBase):
    pass


class Detection(DetectionBase):
    id: UUID

    class Config:
        orm_mode = True
