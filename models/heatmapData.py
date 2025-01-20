from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Float, Boolean, Enum as SQLAlchemyEnum
from datetime import datetime, timezone
import uuid
from .base import Base
from sqlalchemy.orm import relationship
import enum
import numpy as np

class ZoneActivity(str, enum.Enum):
    BROWSING = "browsing"
    INTERACTING = "interacting"
    CHECKOUT = "checkout"
    PROMOTION = "promotion"
    FEATURE = "feature"
    NEW_ARRIVAL = "new_arrival"

class HeatmapData(Base):
    __tablename__ = "heatmap_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)

    # Dwell Time Analysis
    dwell_duration = Column(Float, nullable=True)  # Time spent at point in seconds
    is_stationary = Column(Boolean, default=False)  # If point represents stationary period

    # Interaction Analysis
    activity_type = Column(SQLAlchemyEnum(ZoneActivity), nullable=True)
    interaction_score = Column(Float, default=0.0)  # 0-1 scale of interaction intensity

    # Zone Context
    is_hot_zone = Column(Boolean, default=False)  # High traffic/interaction area
    is_promotion_area = Column(Boolean, default=False)  # Promotional zone
    is_checkout_area = Column(Boolean, default=False)  # Checkout zone
    is_feature_area = Column(Boolean, default=False)  # Featured items area
    is_new_arrival = Column(Boolean, default=False)  # New arrivals area

    # Additional Metrics
    conversion_potential = Column(Float, nullable=True)  # Likelihood of purchase
    engagement_level = Column(Integer, nullable=True)  # 1-5 scale of engagement
    repeat_visit = Column(Boolean, default=False)  # If point is from repeat visitor

    # Metadata
    zone_context = Column(JSON, nullable=True)  # Additional zone information

    # Relationships
    zone = relationship("Zone", back_populates="heatmap_data")

    def __repr__(self):
        return f"<HeatmapData(camera_id={self.camera_id}, timestamp={self.timestamp}, x={self.x}, y={self.y}, weight={self.weight}, zone_id={self.zone_id})>"

    def calculate_intensity(self):
        """Calculate weighted intensity based on dwell time and interaction"""
        base_intensity = self.weight
        if self.dwell_duration:
            base_intensity *= (1 + min(self.dwell_duration / 300, 1))  # Max 2x for 5 min dwell
        if self.interaction_score:
            base_intensity *= (1 + self.interaction_score)  # Max 2x for full interaction
        return base_intensity

    def get_zone_metrics(self):
        """Get comprehensive zone metrics"""
        return {
            "is_hot_zone": self.is_hot_zone,
            "dwell_time": self.dwell_duration,
            "interaction_score": self.interaction_score,
            "conversion_potential": self.conversion_potential,
            "engagement_level": self.engagement_level,
            "activity_type": self.activity_type.value if self.activity_type else None
        }

    @property
    def is_active_zone(self):
        """Determine if this is an active zone based on metrics"""
        return (self.is_hot_zone or
                self.interaction_score > 0.7 or
                (self.dwell_duration and self.dwell_duration > 120))