from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum


# Enums
class EventType(PyEnum):
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PACKAGE_THEFT = "PACKAGE_THEFT"
    SMOKE_DETECTED = "SMOKE_DETECTED"
    SUSPICIOUS_BEHAVIOR = "SUSPICIOUS_BEHAVIOR"


class EventSeverity(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(PyEnum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    type = Column(Enum(EventType), nullable=False)
    severity = Column(Enum(EventSeverity), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.NEW, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    evidence = Column(JSON, nullable=True)  # List of Detection IDs or data
    meta_data = Column(JSON, nullable=True)  # Additional metadata as JSON

    # Relationships
    property = relationship("Property", back_populates="security_events")
    zone = relationship("Zone", back_populates="security_events")
