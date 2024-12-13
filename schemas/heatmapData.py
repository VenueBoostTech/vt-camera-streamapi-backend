from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID


class HeatmapDataBase(BaseModel):
    zone_id: UUID
    timestamp: datetime
    resolution: Dict[str, int]  # Example: {"width": 1920, "height": 1080}
    data: bytes  # Heatmap data as binary
    meta_data: Optional[Dict]  # Additional metadata as JSON

class HeatmapDataCreate(HeatmapDataBase):
    pass

class HeatmapData(HeatmapDataBase):
    id: UUID

    class Config:
        orm_mode = True
