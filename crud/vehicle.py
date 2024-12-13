from sqlalchemy.orm import Session
from typing import List, Optional
from crud.base import CRUDBase
from models.vehicle import Vehicle, ParkingSpot, ValetRequest
from schemas.vehicle import VehicleCreate, VehicleUpdate, ParkingSpotCreate, ParkingSpotUpdate, ValetRequestCreate, ValetRequestUpdate


class CRUDVehicle(CRUDBase[Vehicle, VehicleCreate, VehicleUpdate]):
    def get_by_license_plate(self, db: Session, license_plate: str):
        return db.query(self.model).filter(self.model.plate_number == license_plate).first()

    def get_by_property(self, db: Session, property_id: str, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        return (
            db.query(self.model)
            .filter(self.model.property_id == property_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDParkingSpot(CRUDBase[ParkingSpot, ParkingSpotCreate, ParkingSpotUpdate]):
    def get_available_spots(self, db: Session, skip: int = 0, limit: int = 100) -> List[ParkingSpot]:
        return (
            db.query(self.model)
            .filter(self.model.is_occupied == False)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDValetRequest(CRUDBase[ValetRequest, ValetRequestCreate, ValetRequestUpdate]):
    def get_active_requests(self, db: Session, skip: int = 0, limit: int = 100) -> List[ValetRequest]:
        return (
            db.query(self.model)
            .filter(self.model.end_time == None)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_duration(self, db: Session, obj_in: ValetRequestCreate) -> ValetRequest:
        """
        Creates a new valet request with the calculated duration if end_time is provided.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            duration=(obj_in.end_time - obj_in.start_time).total_seconds() / 60 if obj_in.end_time else None
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


vehicle = CRUDVehicle(Vehicle)
parking_spot = CRUDParkingSpot(ParkingSpot)
valet_request = CRUDValetRequest(ValetRequest)
