from sqlalchemy import Column, Integer, String, DateTime, Float
from .base import Base

class ThreatDetection(Base):
    __tablename__ = "threat_detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    threat_type = Column(String)
    confidence = Column(Float)
    bbox = Column(String)  # Store as JSON string