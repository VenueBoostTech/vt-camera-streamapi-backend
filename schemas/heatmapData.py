from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

class ZoneActivity(str, Enum):
    BROWSING = "browsing"
    INTERACTING = "interacting"
    CHECKOUT = "checkout"
    PROMOTION = "promotion"
    FEATURE = "feature"
    NEW_ARRIVAL = "new_arrival"

class HeatmapPoint(BaseModel):
    camera_id: str
    timestamp: datetime
    x: float
    y: float
    weight: float
    zone_id: str
    dwell_duration: Optional[float] = None
    activity_type: Optional[ZoneActivity] = None
    interaction_score: Optional[float] = Field(None, ge=0, le=1)
    engagement_level: Optional[int] = Field(None, ge=1, le=5)

class ZoneContext(BaseModel):
    is_hot_zone: bool = False
    is_promotion_area: bool = False
    is_checkout_area: bool = False
    is_feature_area: bool = False
    is_new_arrival: bool = False
    zone_type: str
    current_capacity: Optional[int] = None

class HeatmapDataCreate(BaseModel):
    points: List[HeatmapPoint]
    zone_context: Optional[ZoneContext] = None

class HeatmapMetrics(BaseModel):
    avg_dwell_time: float
    interaction_rate: float
    conversion_potential: float
    engagement_score: float

class HotZoneInfo(BaseModel):
    zone_id: str
    activity_level: float
    peak_times: List[str]
    popular_activities: List[ZoneActivity]

class ZoneAnalytics(BaseModel):
    zone_id: str
    metrics: HeatmapMetrics
    hot_zones: List[HotZoneInfo]
    active_areas: Dict[str, float]
    new_arrivals: List[Dict[str, str]]
    promotion_performance: Dict[str, float]
    checkout_efficiency: Dict[str, float]
    featured_items_engagement: Dict[str, float]

class HeatmapPointResponse(BaseModel):
    camera_id: str
    timestamp: str
    x: float
    y: float
    weight: float
    zone_id: str
    metrics: Optional[HeatmapMetrics] = None
    zone_context: Optional[ZoneContext] = None

class HeatmapDataResponse(BaseModel):
    points: List[HeatmapPointResponse]
    analytics: Optional[ZoneAnalytics] = None

    class Config:
        orm_mode = True

class RetailAnalyticsResponse(BaseModel):
    avg_dwell_time: Dict[str, float]  # By zone
    interaction_rates: Dict[str, float]  # By zone
    hot_zones: List[HotZoneInfo]
    active_zones: Dict[str, List[str]]  # Zone IDs and peak times
    new_arrivals_performance: Dict[str, Dict[str, float]]
    promotion_effectiveness: Dict[str, Dict[str, float]]
    checkout_metrics: Dict[str, Dict[str, float]]
    featured_items: Dict[str, Dict[str, float]]

    class Config:
        orm_mode = True