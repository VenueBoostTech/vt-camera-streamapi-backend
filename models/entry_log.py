from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class EntryLog(Base):
    __tablename__ = "entry_logs"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    person_id = Column(String, index=True)
    gender = Column(String)
    age = Column(String)