from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .base import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, unique=True, index=True)
    rtsp_url = Column(String)
    status = Column(Boolean, default=True)
    last_active = Column(DateTime)
    property_id = Column(String, nullable=True)
    zone_id = Column(String, nullable=True)
    capabilities = Column(String)  # JSON encoded