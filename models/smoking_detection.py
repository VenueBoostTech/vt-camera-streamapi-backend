from sqlalchemy import Column, Integer, String, DateTime, Float
from .base import Base

class SmokingDetection(Base):
    __tablename__ = "smoking_detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    confidence = Column(Float)
    bbox = Column(String)  # Store as JSON string