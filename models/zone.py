from sqlalchemy import Column, String, Integer, ForeignKey, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum
import uuid

class ZoneType(str, Enum):
    ENTRANCE = "ENTRANCE"
    LOBBY = "LOBBY"
    HALLWAY = "HALLWAY"
    STAIRWELL = "STAIRWELL"
    GARAGE = "GARAGE"
    OFFICE_ROOM = "OFFICE_ROOM"
    MEETING_ROOM = "MEETING_ROOM"
    APARTMENT = "APARTMENT"
    RETAIL_SPACE = "RETAIL_SPACE"
    STORAGE_ROOM = "STORAGE_ROOM"
    BATHROOM = "BATHROOM"
    KITCHEN = "KITCHEN"
    GYM = "GYM"
    LAUNDRY = "LAUNDRY"
    RESTRICTED = "RESTRICTED"
    UTILITY = "UTILITY"
    SERVER_ROOM = "SERVER_ROOM"
    OUTDOOR = "OUTDOOR"
    PARKING_LOT = "PARKING_LOT"
    GARDEN = "GARDEN"
    ROOFTOP = "ROOFTOP"

class Zone(Base):
    __tablename__ = "zones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    floor_id = Column(String, ForeignKey("floors.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    type = Column(SQLAlchemyEnum(ZoneType), nullable=False)
    polygon = Column(String)  # JSON-encoded
    rules = Column(String)  # JSON-encoded
    settings = Column(String)  # JSON-encoded
    active = Column(Integer, nullable=True)
    access_level = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)
    square_footage = Column(Float, nullable=True)

    # Relationships
    property = relationship("Property", back_populates="zones")
    floor = relationship("Floor", back_populates="zones")
    cameras = relationship("Camera", back_populates="zone")

    # Analytics and events
    patterns = relationship("Pattern", back_populates="zone")
    behaviors = relationship("Behavior", back_populates="zone")
    space_analytics = relationship("SpaceAnalytics", back_populates="zone")
    heatmap_data = relationship("HeatmapData", back_populates="zone")
    demographics = relationship("Demographics", back_populates="zone")
    security_events = relationship("SecurityEvent", back_populates="zone")
    parking_events = relationship("ParkingEvent", back_populates="zone")
    parking_analytics = relationship("ParkingAnalytics", back_populates="zone")