from sqlalchemy import Column, String, Float, Boolean, Integer
from .base import Base

class SmokeDetection(Base):
    __tablename__ = "smoke_detections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String)
    intensity = Column(Float)
    is_alarm_triggered = Column(Boolean, default=False)