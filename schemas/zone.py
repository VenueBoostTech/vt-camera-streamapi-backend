from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from models.zone import ZoneType

class ZoneCreate(BaseModel):
    name: str
    type: ZoneType
    polygon: str
    rules: str
    settings: str
    active: bool

class ZoneResponse(BaseModel):
    id: UUID
    property_id: UUID
    name: str
    type: ZoneType
    polygon: str
    rules: str
    settings: str
    active: bool

    class Config:
        from_attributes = True
