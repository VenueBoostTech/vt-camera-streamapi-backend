from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime, timezone
from .base import Base
from sqlalchemy.orm import relationship


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    vt_platform_id = Column(String, unique=True, nullable=False, index=True)
    api_key = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_local_test = Column(Boolean, default=True)
    is_prod_test = Column(Boolean, default=True)

    cameras = relationship("Camera", back_populates="business")
    zones = relationship("Zone", back_populates="business")
    properties = relationship("Property", back_populates="business", cascade="all, delete-orphan")
    buildings = relationship("Building", back_populates="business", cascade="all, delete-orphan")