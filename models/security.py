from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from .base import Base
import enum

class ThreatSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ThreatDetection(Base):
    __tablename__ = "security_threat_detections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    location = Column(String)
    severity = Column(Enum(ThreatSeverity))
    description = Column(String)

class SleepingDetection(Base):
    __tablename__ = "sleeping_detections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    timestamp = Column(DateTime(timezone=True))
    duration = Column(Float)