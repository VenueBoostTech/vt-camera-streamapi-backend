from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from .base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    license_plate = Column(String, unique=True, index=True)

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