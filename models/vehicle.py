from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum
from .base import Base
from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
import uuid

class VehicleStatus(PyEnum):
    RESIDENT = "RESIDENT"
    VISITOR = "VISITOR"
    DELIVERY = "DELIVERY"
    UNAUTHORIZED = "UNAUTHORIZED"

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    plate_number = Column(String, unique=True, index=True, nullable=True)
    type = Column(String, nullable=False)
    status = Column(Enum(VehicleStatus), nullable=False, default=VehicleStatus.VISITOR)
    first_seen = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_seen = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    visit_count = Column(Integer, nullable=False, default=0)

    # Relationships (if needed)
    parking_events = relationship("ParkingEvent", back_populates="vehicle")

class ParkingSpot(Base):
    __tablename__ = "parking_spots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String, unique=True)
    is_occupied = Column(Boolean, default=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)

class ValetRequest(Base):
    __tablename__ = "valet_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float)