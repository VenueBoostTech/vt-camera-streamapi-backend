from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ParkingAnalyticsBase(BaseModel):
    zone_id: UUID
    timestamp: datetime
    total_spots: int
    occupied_spots: int
    resident_vehicles: int
    visitor_vehicles: int
    violations: int


class ParkingAnalyticsCreate(ParkingAnalyticsBase):
    pass


class ParkingAnalyticsUpdate(BaseModel):
    total_spots: Optional[int] = None
    occupied_spots: Optional[int] = None
    resident_vehicles: Optional[int] = None
    visitor_vehicles: Optional[int] = None
    violations: Optional[int] = None


class ParkingAnalytics(ParkingAnalyticsBase):
    id: UUID

    class Config:
        orm_mode = True
