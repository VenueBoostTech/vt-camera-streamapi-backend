from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from datetime import datetime, timezone
import uuid
from .base import Base
from sqlalchemy.orm import relationship


class Demographics(Base):
    __tablename__ = "demographics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as a string
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    total_count = Column(Integer, nullable=False, default=0)
    age_groups = Column(JSON, nullable=False)  
    gender_distribution = Column(JSON, nullable=False)
    zone = relationship("Zone", back_populates="demographics")

    @property
    def total_count(self):
        return self._total_count

    @total_count.setter
    def total_count(self, value):
        if value < 0:
            raise ValueError("total_count cannot be negative")
        self._total_count = value

    def compute_total_count(self): return sum(age_group["count"] for age_group in self.age_groups) if self.age_groups else 0
