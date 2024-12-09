from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VehicleBase(BaseModel):
    type: str
    license_plate: str

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime

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