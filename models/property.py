from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DateTime, Float, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum
import uuid


# Enums
class PropertyType(str, Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    MIXED = "MIXED"

class ZoneType(str, Enum):
    ENTRANCE = "ENTRANCE"
    LOBBY = "LOBBY"
    PARKING = "PARKING"
    COMMON_AREA = "COMMON_AREA"
    GARAGE = "GARAGE"
    RETAIL = "RETAIL"
    SERVICE = "SERVICE"

class CameraType(str, Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    THERMAL = "THERMAL"

class Status(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"

class Property(Base):
    __tablename__ = "properties"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    type = Column(SQLAlchemyEnum(PropertyType))
    address = Column(String)
    settings = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Zone(Base):
    __tablename__ = "zones"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Store UUID as a string
    property_id = Column(String, ForeignKey("properties.id"))
    name = Column(String, index=True)
    type = Column(SQLAlchemyEnum(ZoneType))
    polygon = Column(String)  # JSON encoded
    rules = Column(String)  # JSON encoded
    settings = Column(String)  # JSON encoded
    active = Column(Integer)