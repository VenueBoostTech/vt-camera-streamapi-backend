from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class StaffBase(BaseModel):
    name: str
    position: str

class StaffCreate(StaffBase):
    pass

class StaffUpdate(StaffBase):
    pass

class Staff(StaffBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class WorkSessionBase(BaseModel):
    staff_id: int
    start_time: datetime
    end_time: datetime
    total_duration: float

class WorkSessionCreate(WorkSessionBase):
    pass

class WorkSession(WorkSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ActivityBase(BaseModel):
    work_session_id: int
    type: str
    duration: float

class ActivityCreate(ActivityBase):
    pass

class Activity(ActivityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BreakBase(BaseModel):
    staff_id: int
    start_time: datetime
    end_time: datetime
    duration: float

class BreakCreate(BreakBase):
    pass

class Break(BreakBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
