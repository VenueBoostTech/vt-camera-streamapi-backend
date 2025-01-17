from sqlalchemy import Column, Integer, String, DateTime
from .base import Base
import uuid

class EntryLog(Base):
    __tablename__ = "entry_logs"

    id = id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, index=True, nullable=True)
    person_id = Column(String, index=True, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(String, nullable=True)
    entering = Column(Integer)
    exiting = Column(Integer) 
    in_store = Column(Integer)