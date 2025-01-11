from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class HeatmapPoint(BaseModel):
    camera_id: str
    timestamp: datetime
    x: float
    y: float
    weight: float
    zone_id: str


class HeatmapDataCreate(BaseModel):
    points: List[HeatmapPoint]  # List of heatmap points


class HeatmapPointResponse(BaseModel):
    camera_id: str
    timestamp: str
    x: float
    y: float
    weight: float
    zone_id: str

class HeatmapDataResponse(BaseModel):
    points: List[HeatmapPointResponse]

    class Config:
        orm_mode = True
