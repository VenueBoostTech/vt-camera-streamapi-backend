from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime, timezone
import uuid


class Detection(Base):
    __tablename__ = "detections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    type = Column(String, nullable=False)
    bbox = Column(JSON, nullable=True)  # BoundingBox as JSON
    confidence = Column(Float, nullable=False)
    tracking_id = Column(String, nullable=True)
    attributes = Column(JSON, nullable=True)  # Additional attributes as JSON

    # Relationships
    camera = relationship("Camera", back_populates="detections")

