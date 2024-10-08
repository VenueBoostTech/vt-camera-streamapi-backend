from pydantic import BaseModel
from datetime import datetime

class ExitLogBase(BaseModel):
    camera_id: str
    timestamp: datetime
    person_id: str

class ExitLogCreate(ExitLogBase):
    pass

class ExitLog(ExitLogBase):
    id: int

    class Config:
        orm_mode = True