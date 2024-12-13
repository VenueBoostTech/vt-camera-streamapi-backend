from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base
import uuid

class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=True)
    type = Column(String, nullable=False)  # Type of the pattern
    analysis_period = Column(JSON)  # JSON object to store time range (e.g., {"start": ..., "end": ...})
    detection_count = Column(Integer, default=0)
    pattern_data = Column(JSON)  # JSON to store additional pattern-related data
    confidence = Column(Float, default=0.0)

    property = relationship("Property", back_populates="patterns")
    zone = relationship("Zone", back_populates="patterns")
