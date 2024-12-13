from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from enum import Enum
from sqlalchemy.types import Enum as SQLAlchemyEnum  # Use SQLAlchemy Enum


class PatternType(str, Enum):
    RECURRING = "RECURRING"
    ANOMALY = "ANOMALY"
    SUSPICIOUS = "SUSPICIOUS"


class Behavior(Base):
    __tablename__ = "behaviors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=True)
    pattern_type = Column(SQLAlchemyEnum(PatternType), nullable=False)
    activity_type = Column(String)
    frequency = Column(Integer)
    confidence = Column(Float)
    last_detected = Column(DateTime)

    property = relationship("Property", back_populates="behaviors")
    zone = relationship("Zone", back_populates="behaviors")
