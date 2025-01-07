from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from uuid import UUID


class DemographicsBase(BaseModel):
    zone_id: str
    timestamp: datetime
    total_count: int
    age_groups: Dict[str, int]
    gender_distribution: Dict[str, int]

class DemographicsCreate(DemographicsBase):
    pass

class Demographics(DemographicsBase):
    id: UUID

    class Config:
        orm_mode = True
