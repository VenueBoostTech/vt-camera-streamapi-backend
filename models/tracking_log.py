from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class TrackingLog(Base):
    __tablename__ = "tracking_logs"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    person_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    bbox = Column(String)  # Store as JSON string
    centroid = Column(String)  # Store as JSON string