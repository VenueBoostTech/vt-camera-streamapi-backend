from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class FootpathAnalyticsBase(BaseModel):
    zone_id: str
    traffic_count: int
    unique_visitors: int
    avg_dwell_time: Optional[float] = None
    max_dwell_time: Optional[float] = None
    total_dwell_time: Optional[float] = None
    heatmap_data: Optional[Dict[str, Any]] = None

class FootpathAnalyticsCreate(FootpathAnalyticsBase):
    pass

class FootpathAnalytics(FootpathAnalyticsBase):
    id: str
    business_id: str
    property_id: str
    timestamp: datetime

    class Config:
        orm_mode = True

class FootpathPatternBase(BaseModel):
    zone_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    frequency: int = 1
    avg_duration: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class FootpathPatternCreate(FootpathPatternBase):
    pass

class FootpathPattern(FootpathPatternBase):
    id: str
    business_id: str
    property_id: str
    timestamp: datetime

    class Config:
        orm_mode = True