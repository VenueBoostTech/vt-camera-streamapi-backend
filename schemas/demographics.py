from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from uuid import UUID


class DemographicsBase(BaseModel):
    zone_id: UUID
    timestamp: datetime
    total_count: int
    age_groups: Dict[str, int]  # Example: {"18-25": 20, "26-35": 30}
    gender_distribution: Dict[str, int]  # Example: {"male": 50, "female": 50}

class DemographicsCreate(DemographicsBase):
    pass

class Demographics(DemographicsBase):
    id: UUID

    class Config:
        orm_mode = True
