from pydantic import BaseModel
from typing import Dict, Optional
from uuid import UUID
from enum import Enum
from models.zone import ZoneType


class ZoneCreate(BaseModel):
    property_id: str
    building_id: str
    floor_id: str
    name: str
    type: ZoneType
    polygon: Optional[str] = None
    rules: Optional[str] = None
    settings: Optional[str] = None
    active: Optional[int] = None
    access_level: Optional[str] = None
    capacity: Optional[int] = None 
    square_footage: Optional[float] = None


class ZoneResponse(BaseModel):
    id: str
    property_id: str
    building_id: str
    floor_id: str
    name: str
    type: ZoneType
    polygon: Optional[str] = None
    rules: Optional[str] = None
    settings: Optional[str] = None
    active: Optional[int] = None
    access_level: Optional[str] = None
    capacity: Optional[int] = None
    square_footage: Optional[float] = None

    class Config:
        from_attributes = True