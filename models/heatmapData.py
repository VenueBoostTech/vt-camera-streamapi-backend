from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, LargeBinary
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
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    resolution = Column(JSON, nullable=False)  # Store resolution as JSON (e.g., {"width": 1920, "height": 1080})
    data = Column(LargeBinary, nullable=False)  # Store the heatmap data as binary
    meta_data = Column(JSON, nullable=True)  # Additional metadata about the heatmap
    zone = relationship("Zone", back_populates="heatmap_data")


    def encode_data(self, array: np.ndarray) -> bytes:
        """Encode NumPy array to binary format."""
        return array.tobytes()

    def decode_data(self) -> np.ndarray:
        """Decode binary data to NumPy array."""
        return np.frombuffer(self.data, dtype=np.float32)
