from pydantic import BaseModel
from typing import Dict
from uuid import UUID
from datetime import datetime
from models.property import PropertyType

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class PropertyCreate(BaseModel):
    name: str
    type: PropertyType
    address: str
    settings: str
    created_at: datetime
    updated_at: datetime

    def model_dump(self):
        data = super().model_dump()
        data['id'] = str(data['id'])  # Convert UUID to string
        return data

class PropertyResponse(BaseModel):
    id: UUID
    name: str
    type: PropertyType
    address: str
    settings: str
    created_at: datetime
    updated_at: datetime

    def model_dump(self):
        data = super().model_dump()
        data['id'] = str(data['id'])  # Convert UUID to string
        return data

    class Config:
        from_attributes = True