from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum
import uuid
from sqlalchemy.types import TypeDecorator, JSON

import json

# Enums
class PropertyType(str, Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    MIXED = "MIXED"

class BuildingType(str, Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    MIXED = "MIXED"

class JSONString(TypeDecorator):
    impl = JSON
    
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value
class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    type = Column(SQLAlchemyEnum(PropertyType))
    address = Column(String)
    settings = Column(JSONString, nullable=True, default={})  # Using ur custom type
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # Relationships
    zones = relationship("Zone", back_populates="property")
    behaviors = relationship("Behavior", back_populates="property")
    patterns = relationship("Pattern", back_populates="property")
    buildings = relationship("Building", back_populates="property", cascade="all, delete-orphan")  # Added relationship for buildings

    security_events = relationship("SecurityEvent", back_populates="property")
    incidents = relationship("Incident", back_populates="property")

class Building(Base):
    __tablename__ = "buildings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(SQLAlchemyEnum(BuildingType), nullable=False)
    sub_address = Column(String, nullable=True)
    settings = Column(JSONString, nullable=True, default={})  # Using our custom type


    # Relationships
    property = relationship("Property", back_populates="buildings")
    floors = relationship("Floor", back_populates="building")
    zones = relationship("Zone", back_populates="building")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    floor_number = Column(Integer, nullable=False)
    layout = Column(String, nullable=True)

    # Relationships
    building = relationship("Building", back_populates="floors")
    zones = relationship("Zone", back_populates="floor")
