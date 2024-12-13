from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID  # If using PostgreSQL
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime, timezone


class SpaceAnalytics(Base):
    __tablename__ = "space_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    occupancy = Column(Integer, nullable=False)
    demographics = Column(JSON, nullable=True)  # Store demographics as JSON
    heatmap_data = Column(LargeBinary, nullable=True)  # Heatmap data as binary (e.g., image data)
    flow_patterns = Column(JSON, nullable=True)  # Store flow pattern data as JSON
    peak_times = Column(JSON, nullable=True)  # Store peak times as a list of time ranges

    # Relationships
    zone = relationship("Zone", back_populates="space_analytics")