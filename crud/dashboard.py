from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
from models.staff import Staff, WorkSession, Break
from models.security import ThreatDetection, SleepingDetection
from models.environment import SmokeDetection
from models.vehicle import Vehicle, ParkingSpot, ValetRequest
from schemas.dashboard import MonitoringSummary

def get_monitoring_summary(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> MonitoringSummary:
    query = db.query(
        func.count(distinct(Staff.id)).label('total_staff'),
        func.count(WorkSession.id).label('total_work_sessions'),
        func.count(Break.id).label('total_breaks'),
        func.avg(WorkSession.total_duration).label('average_work_duration'),
        func.avg(Break.duration).label('average_break_duration'),
        func.count(ThreatDetection.id).label('total_threats'),
        func.sum(case((ThreatDetection.severity == 'HIGH', 1), else_=0)).label('high_severity_threats'),
        func.sum(case((ThreatDetection.severity == 'MEDIUM', 1), else_=0)).label('medium_severity_threats'),
        func.sum(case((ThreatDetection.severity == 'LOW', 1), else_=0)).label('low_severity_threats'),
        func.count(SleepingDetection.id).label('total_sleeping_detections'),
        func.count(SmokeDetection.id).label('total_smoke_detections'),
        func.sum(case((SmokeDetection.is_alarm_triggered == True, 1), else_=0)).label('active_smoke_alarms'),
        func.count(Vehicle.id).label('total_vehicles'),
        func.count(ParkingSpot.id).label('total_parking_spots'),
        func.sum(case((ParkingSpot.is_occupied == True, 1), else_=0)).label('occupied_parking_spots'),
        func.count(ValetRequest.id).label('total_valet_requests'),
        func.sum(case((ValetRequest.end_time == None, 1), else_=0)).label('active_valet_requests')
    )

    if start_date:
        query = query.filter(WorkSession.start_time >= start_date)
    if end_date:
        query = query.filter(WorkSession.end_time <= end_date)

    result = query.first()

    return MonitoringSummary(
        total_staff=result.total_staff,
        total_work_sessions=result.total_work_sessions,
        total_breaks=result.total_breaks,
        average_work_duration=float(result.average_work_duration or 0),
        average_break_duration=float(result.average_break_duration or 0),
        total_threats=result.total_threats,
        high_severity_threats=result.high_severity_threats,
        medium_severity_threats=result.medium_severity_threats,
        low_severity_threats=result.low_severity_threats,
        total_sleeping_detections=result.total_sleeping_detections,
        total_smoke_detections=result.total_smoke_detections,
        active_smoke_alarms=result.active_smoke_alarms,
        total_vehicles=result.total_vehicles,
        total_parking_spots=result.total_parking_spots,
        occupied_parking_spots=result.occupied_parking_spots,
        total_valet_requests=result.total_valet_requests,
        active_valet_requests=result.active_valet_requests,
        start_date=start_date,
        end_date=end_date
    )