from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, LargeBinary, Float
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID  # If using PostgreSQL
import numpy as np
import json
from datetime import datetime, timezone
import uuid 
from .base import Base
from sqlalchemy.orm import relationship

class HeatmapData(Base):
    __tablename__ = "heatmap_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as a string
    camera_id = Column(String, nullable=False)  # Identifier for the camera
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))  # Timestamp of the heatmap point
    x = Column(Float, nullable=False)  # X coordinate of the point
    y = Column(Float, nullable=False)  # Y coordinate of the point
    weight = Column(Float, nullable=False)  # Weight value for the point
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)  # Zone ID
    zone = relationship("Zone", back_populates="heatmap_data")  # Relationship with Zone

    def __repr__(self):
        return f"<HeatmapData(camera_id={self.camera_id}, timestamp={self.timestamp}, x={self.x}, y={self.y}, weight={self.weight}, zone_id={self.zone_id})>"

