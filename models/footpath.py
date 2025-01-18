from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base
import uuid

class FootpathAnalytics(Base):
    __tablename__ = "footpath_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    traffic_count = Column(Integer, nullable=False, default=0)
    unique_visitors = Column(Integer, nullable=False, default=0)
    avg_dwell_time = Column(Float, nullable=True)
    max_dwell_time = Column(Float, nullable=True)
    total_dwell_time = Column(Float, nullable=True)
    heatmap_data = Column(JSON, nullable=True)

    # Relationships
    zone = relationship("Zone", back_populates="footpath_analytics")
    business = relationship("Business")
    property = relationship("Property")

class FootpathPattern(Base):
    __tablename__ = "footpath_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    pattern_type = Column(String, nullable=False)  # e.g., 'zone_sequence', 'dwell_pattern'
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    pattern_data = Column(JSON, nullable=False)  # Store sequence of zones or pattern data
    frequency = Column(Integer, nullable=False, default=1)
    avg_duration = Column(Float, nullable=True)  # Average time to complete pattern
    confidence = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional pattern metadata

    # Relationships
    zone = relationship("Zone", back_populates="footpath_patterns")
    business = relationship("Business")
    property = relationship("Property")