from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True)
    position = Column(String)
    
    work_sessions = relationship("WorkSession", back_populates="staff")
    breaks = relationship("Break", back_populates="staff")

class WorkSession(Base):
    __tablename__ = "work_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    total_duration = Column(Float)
    
    staff = relationship("Staff", back_populates="work_sessions")
    activities = relationship("Activity", back_populates="work_session")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_session_id = Column(Integer, ForeignKey("work_sessions.id"))
    type = Column(String)
    duration = Column(Float)
    
    work_session = relationship("WorkSession", back_populates="activities")

class Break(Base):
    __tablename__ = "breaks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float)
    
    staff = relationship("Staff", back_populates="breaks")