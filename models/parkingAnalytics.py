from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from .base import Base
from uuid import uuid4
from datetime import datetime


class ParkingAnalytics(Base):
    __tablename__ = "parking_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_spots = Column(Integer, nullable=False)
    occupied_spots = Column(Integer, nullable=False)
    resident_vehicles = Column(Integer, nullable=False, default=0)
    visitor_vehicles = Column(Integer, nullable=False, default=0)
    violations = Column(Integer, nullable=False, default=0)

    # Relationships
    zone = relationship("Zone", back_populates="parking_analytics")
