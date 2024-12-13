from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PatternBase(BaseModel):
    property_id: Optional[str]
    zone_id: Optional[str]
    type: str
    analysis_period: Dict[str, datetime]  # Expecting a JSON object with "start" and "end"
    detection_count: int
    pattern_data: Dict  # Additional pattern data
    confidence: float

class PatternCreate(PatternBase):
    pass

class Pattern(PatternBase):
    id: str

    class Config:
        orm_mode = True
