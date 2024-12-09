from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.vehicle import Vehicle, ParkingSpot, ValetRequest
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, ParkingSpotCreate, ParkingSpotUpdate, ValetRequestCreate, ValetRequestUpdate

class CRUDVehicle(CRUDBase[Vehicle, VehicleCreate, VehicleUpdate]):
    def get_by_license_plate(self, db: Session, license_plate: str):
        return db.query(self.model).filter(self.model.license_plate == license_plate).first()

class CRUDParkingSpot(CRUDBase[ParkingSpot, ParkingSpotCreate, ParkingSpotUpdate]):
    def get_available_spots(self, db: Session):
        return db.query(self.model).filter(self.model.is_occupied == False).all()

class CRUDValetRequest(CRUDBase[ValetRequest, ValetRequestCreate, ValetRequestUpdate]):
    def get_active_requests(self, db: Session):
        return db.query(self.model).filter(self.model.end_time == None).all()

vehicle = CRUDVehicle(Vehicle)
parking_spot = CRUDParkingSpot(ParkingSpot)
valet_request = CRUDValetRequest(ValetRequest)