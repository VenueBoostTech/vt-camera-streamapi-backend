from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from models.property import PropertyType, BuildingType

# Address model
class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str


class BuildingCreate(BaseModel):
    name: str
    type: BuildingType  # Enum: BuildingType (e.g., RESIDENTIAL, COMMERCIAL, MIXED)
    sub_address: Optional[str] = None  # Optional field for sub-address
    settings: Optional[dict] = Field(default_factory=dict)  # JSON-compatible settings
    property_id: str

class BuildingCreateNested(BaseModel):
    name: str
    type: BuildingType  
    sub_address: Optional[str] = None  
    settings: Optional[dict] = Field(default_factory=dict)

# PropertyCreate model
class PropertyCreate(BaseModel):
    name: str
    type: PropertyType
    address: str
    settings: Optional[dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    buildings: List[BuildingCreateNested] = Field(default_factory=list)

# PropertyResponse model
class PropertyResponse(BaseModel):
    id: UUID
    name: str
    type: PropertyType
    address: str
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# BuildingResponse model
class BuildingResponse(BaseModel):
    id: UUID
    property_id: UUID
    name: str
    type: BuildingType
    sub_address: Optional[str] = None
    settings: Optional[dict] = Field(default_factory=dict)

    class Config:
        orm_mode = True

# FloorCreate model
class FloorCreate(BaseModel):
    building_id: str
    floor_number: int
    layout: Optional[str] = None

# FloorResponse model
class FloorResponse(BaseModel):
    id: UUID
    building_id: UUID
    floor_number: int
    layout: Optional[str] = None

    class Config:
        orm_mode = True

# Extended PropertyResponse with buildings
class ExtendedPropertyResponse(PropertyResponse):
    buildings: List[BuildingResponse] = Field(default_factory=list)

# Extended BuildingResponse with floors
class ExtendedBuildingResponse(BuildingResponse):
    floors: List[FloorResponse] = Field(default_factory=list)
