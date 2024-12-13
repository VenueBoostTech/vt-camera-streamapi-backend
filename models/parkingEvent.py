from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
from uuid import uuid4, UUID
from enum import Enum as PyEnum

class ParkingEventType(PyEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    VIOLATION = "VIOLATION"

class ParkingEvent(Base):
    __tablename__ = "parking_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    type = Column(Enum(ParkingEventType), nullable=False)  # Enum type
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    parking_spot = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in minutes
    meta_data = Column(JSON, nullable=True)  # Additional metadata as JSON

    # Relationships
    vehicle = relationship("Vehicle", back_populates="parking_events")
    zone = relationship("Zone", back_populates="parking_events")
