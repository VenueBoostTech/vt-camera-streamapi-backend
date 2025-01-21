from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from datetime import datetime, timezone
import uuid
from .base import Base
from sqlalchemy.orm import relationship

class Demographics(Base):
    __tablename__ = "demographics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    # Basic demographics
    total_count = Column(Integer, nullable=False, default=0)
    age_groups = Column(JSON, nullable=False)
    gender_distribution = Column(JSON, nullable=False)

    # Shopping Patterns
    hourly_traffic = Column(JSON, nullable=True)  # Traffic by hour
    daily_traffic = Column(JSON, nullable=True)   # Traffic by day of week
    peak_hours = Column(JSON, nullable=True)      # Peak shopping hours with counts
    off_peak_hours = Column(JSON, nullable=True)  # Off-peak hours with counts

    # Customer Profile
    visit_frequency = Column(JSON, nullable=True)  # First time vs returning
    dwell_time = Column(JSON, nullable=True)      # Time spent in zone
    cross_shopping = Column(JSON, nullable=True)   # Shopping across zones
    customer_segments = Column(JSON, nullable=True)  # Customer segmentation data

    # Zone-specific Demographics
    zone_conversion = Column(JSON, nullable=True)  # Zone entry to purchase ratio
    zone_traffic_flow = Column(JSON, nullable=True)  # Traffic flow patterns
    zone_engagement = Column(JSON, nullable=True)  # Interaction with zone items

    zone = relationship("Zone", back_populates="demographics")

    @property
    def total_count(self):
        return self._total_count

    @total_count.setter
    def total_count(self, value):
        if value < 0:
            raise ValueError("total_count cannot be negative")
        self._total_count = value

    def compute_total_count(self):
        return sum(age_group["count"] for age_group in self.age_groups) if self.age_groups else 0

    def get_peak_shopping_times(self):
        """Get peak shopping hours and their traffic"""
        if not self.peak_hours:
            return None
        return sorted(
            self.peak_hours.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def get_customer_profile(self):
        """Get comprehensive customer profile"""
        return {
            "visit_frequency": self.visit_frequency,
            "dwell_time": self.dwell_time,
            "segments": self.customer_segments
        }

    def get_zone_metrics(self):
        """Get zone-specific metrics"""
        return {
            "conversion": self.zone_conversion,
            "traffic_flow": self.zone_traffic_flow,
            "engagement": self.zone_engagement
        }