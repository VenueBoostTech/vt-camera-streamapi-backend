from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from datetime import datetime, timezone
import uuid 
from .base import Base
from sqlalchemy.orm import relationship

class Demographics(Base):
    __tablename__ = "demographics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as a string
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    total_count = Column(Integer, nullable=False)
    age_groups = Column(JSON, nullable=True)  # Store age groups as JSON (e.g., {"18-25": 20, "26-35": 30})
    gender_distribution = Column(JSON, nullable=True)  # Store gender distribution as JSON (e.g., {"male": 50, "female": 50})
    zone = relationship("Zone", back_populates="demographics")

