from pydantic import BaseModel
from typing import Dict, Optional, List
from uuid import UUID
from enum import Enum
from models.zone import ZoneType
import json

class ZoneCreate(BaseModel):
    property_id: str
    building_id: str
    floor_id: str
    name: str
    type: ZoneType
    polygon: Optional[List[Dict[str, int]]] = None
    rules: Optional[str] = None
    settings: Optional[str] = None
    active: Optional[int] = None
    access_level: Optional[str] = None
    capacity: Optional[int] = None 
    square_footage: Optional[float] = None
    store_id: Optional[str]


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
    store_id : Optional[str] = None

    @classmethod
    def model_validate(cls, obj):
        data = obj.__dict__.copy()
        data['polygon'] = json.loads(obj.polygon) if obj.polygon else None
        return super().model_validate(data)

    class Config:
        from_attributes = True