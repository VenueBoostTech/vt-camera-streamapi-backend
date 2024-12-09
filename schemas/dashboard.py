from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MonitoringSummary(BaseModel):
    total_staff: int
    total_work_sessions: int
    total_breaks: int
    average_work_duration: float
    average_break_duration: float
    total_threats: int
    high_severity_threats: int
    medium_severity_threats: int
    low_severity_threats: int
    total_sleeping_detections: int
    total_smoke_detections: int
    active_smoke_alarms: int
    total_vehicles: int
    total_parking_spots: int
    occupied_parking_spots: int
    total_valet_requests: int
    active_valet_requests: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        orm_mode = True