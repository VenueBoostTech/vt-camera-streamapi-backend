from pydantic import BaseModel
from typing import Optional, Dict, List, Optional
from datetime import datetime
from uuid import UUID


class TimeRange(BaseModel):
    start: datetime
    end: datetime


class SpaceAnalyticsBase(BaseModel):
    zone_id: UUID
    timestamp: datetime
    occupancy: int
    demographics: Dict  # Demographics as a JSON object
    heatmap_data: Optional[bytes]  # Heatmap data as binary
    flow_patterns: Optional[Dict]  # Flow patterns as a JSON object
    peak_times: Optional[List[TimeRange]]  # List of time ranges

class SpaceAnalyticsCreate(SpaceAnalyticsBase):
    pass

class SpaceAnalytics(SpaceAnalyticsBase):
    id: UUID

    class Config:
        orm_mode = True
