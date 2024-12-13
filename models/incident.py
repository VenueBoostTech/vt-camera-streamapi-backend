from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from .base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    related_events = Column(JSON, nullable=True)  # Store as list of strings
    status = Column(String, nullable=False)  # Example: "NEW", "CLOSED"
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(String, nullable=True)

    # Relationships
    property = relationship("Property", back_populates="incidents")
