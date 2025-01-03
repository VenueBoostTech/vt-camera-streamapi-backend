from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum
import uuid

class CameraType(str, Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    THERMAL = "THERMAL"

class CameraStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, unique=True, index=True, nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=True)  # Corrected ForeignKey reference
    rtsp_url = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(CameraStatus), nullable=False, default=CameraStatus.ACTIVE)
    last_active = Column(DateTime, nullable=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    capabilities = Column(String)  # JSON-encoded
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    direction = Column(String, nullable=True)
    coverage_area = Column(JSON, nullable=True)  # Field of view polygon as JSON
    store_id = Column(String, nullable=True) 
    # Relationships
    zone = relationship("Zone", back_populates="cameras")
    detections = relationship("Detection", back_populates="camera")
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    business = relationship("Business", back_populates="cameras")
