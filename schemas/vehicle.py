from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class VehicleBase(BaseModel):
    property_id: UUID
    plate_number: Optional[str] = None
    type: str
    status: str  # Example: "RESIDENT", "VISITOR", "DELIVERY", "UNAUTHORIZED"
    first_seen: datetime
    last_seen: datetime
    visit_count: int


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[datetime] = None
    visit_count: Optional[int] = None


class Vehicle(VehicleBase):
    id: UUID

    class Config:
        orm_mode = True

class ParkingSpotBase(BaseModel):
    number: str
    is_occupied: bool
    vehicle_id: Optional[int] = None

class ParkingSpotCreate(ParkingSpotBase):
    pass

class ParkingSpotUpdate(ParkingSpotBase):
    pass

class ParkingSpot(ParkingSpotBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ValetRequestBase(BaseModel):
    vehicle_id: int
    staff_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None

class ValetRequestCreate(ValetRequestBase):
    pass

class ValetRequestUpdate(ValetRequestBase):
    pass

class ValetRequest(ValetRequestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True