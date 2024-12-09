from pydantic import BaseModel
from datetime import datetime

class EntryLogBase(BaseModel):
    camera_id: str
    timestamp: datetime
    person_id: str
    gender: str
    age: str

class EntryLogCreate(EntryLogBase):
    pass

class EntryLog(EntryLogBase):
    id: int

    class Config:
        orm_mode = True