from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class ExitLog(Base):
    __tablename__ = "exit_logs"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    person_id = Column(String, index=True)