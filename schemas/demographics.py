from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from uuid import UUID

class AgeGroup(BaseModel):
    age: str = Field(..., description="Age group range (e.g., '(25-32)')")
    count: int = Field(ge=0, description="Total count in this age group")
    male: int = Field(ge=0, description="Male count in this age group")
    female: int = Field(ge=0, description="Female count in this age group")

class HourlyPattern(BaseModel):
    hour: int = Field(..., description="Hour of day (0-23)")
    count: int = Field(..., description="Traffic count")
    conversion_rate: Optional[float] = Field(None, description="Conversion rate for this hour")

class CustomerSegment(BaseModel):
    segment_id: str = Field(..., description="Segment identifier")
    count: int = Field(..., description="Number of customers in segment")
    avg_dwell_time: float = Field(..., description="Average dwell time in minutes")
    visit_frequency: Dict[str, int] = Field(..., description="Visit frequency distribution")

class ZoneMetrics(BaseModel):
    traffic_count: int = Field(..., description="Total traffic count")
    conversion_rate: float = Field(..., description="Zone conversion rate")
    avg_dwell_time: float = Field(..., description="Average dwell time in minutes")
    engagement_score: float = Field(..., description="Zone engagement score")

class DemographicsBase(BaseModel):
    zone_id: str = Field(..., description="Unique identifier for the zone")
    timestamp: datetime = Field(..., description="Timestamp for the demographic data")
    total_count: int = Field(default=0, ge=0, description="Total count of individuals")
    age_groups: List[AgeGroup] = Field(..., description="List of age group data")
    gender_distribution: Dict[str, int] = Field(
        ...,
        description="Gender distribution of individuals (e.g., {'Male': 31, 'Female': 22})"
    )

    # Shopping Patterns
    hourly_traffic: Optional[List[HourlyPattern]] = Field(
        None, description="Traffic patterns by hour"
    )
    peak_hours: Optional[Dict[str, int]] = Field(
        None, description="Peak shopping hours with counts"
    )

    # Customer Profile
    customer_segments: Optional[List[CustomerSegment]] = Field(
        None, description="Customer segmentation data"
    )
    visit_frequency: Optional[Dict[str, int]] = Field(
        None, description="Visit frequency distribution"
    )

    # Zone Demographics
    zone_metrics: Optional[ZoneMetrics] = Field(
        None, description="Zone-specific metrics"
    )

class DemographicsCreate(DemographicsBase):
    id: Optional[UUID] = Field(None, description="Optional ID for new demographic data")

class DemographicsResponse(DemographicsBase):
    id: UUID = Field(..., description="Unique identifier for the demographic record")

    class Config:
        orm_mode = True

class PeakShoppingResponse(BaseModel):
    peak_hours: Dict[str, int]
    peak_days: Dict[str, int]
    peak_segments: List[CustomerSegment]

class ShoppingPatternResponse(BaseModel):
    hourly_traffic: List[HourlyPattern]
    daily_distribution: Dict[str, int]
    peak_periods: Dict[str, Dict[str, int]]

class CustomerProfileResponse(BaseModel):
    segments: List[CustomerSegment]
    visit_patterns: Dict[str, int]
    loyalty_distribution: Dict[str, int]

class ZoneDemographicsResponse(BaseModel):
    metrics: ZoneMetrics
    popular_times: Dict[str, List[HourlyPattern]]
    customer_types: List[CustomerSegment]