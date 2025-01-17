from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from uuid import UUID


class AgeGroup(BaseModel):
    age: str = Field(..., description="Age group range (e.g., '(25-32)')")
    count: int = Field(ge=0, description="Total count in this age group")
    male: int = Field(ge=0, description="Male count in this age group")
    female: int = Field(ge=0, description="Female count in this age group")


class DemographicsBase(BaseModel):
    zone_id: str = Field(..., description="Unique identifier for the zone")
    timestamp: datetime = Field(..., description="Timestamp for the demographic data")
    total_count: int = Field(default=0, ge=0, description="Total count of individuals")
    age_groups: List[AgeGroup] = Field(..., description="List of age group data")
    gender_distribution: Dict[str, int] = Field(
        ...,
        description="Gender distribution of individuals (e.g., {'Male': 31, 'Female': 22})"
    )


class DemographicsCreate(DemographicsBase):
    id: Optional[UUID] = Field(None, description="Optional ID for new demographic data")


class Demographics(DemographicsBase):
    id: UUID = Field(..., description="Unique identifier for the demographic record")

    class Config:
        orm_mode = True
