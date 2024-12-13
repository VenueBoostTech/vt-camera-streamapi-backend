from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import crud
import schemas as schemas

router = APIRouter()

# Create a new vehicle
@router.post("/vehicles", response_model=schemas.Vehicle)
async def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle entry.

    - **vehicle**: The details of the vehicle to be created
    """
    return crud.vehicle.create(db, obj_in=vehicle)

# Get vehicles by property ID
@router.get("/properties/{property_id}/vehicles", response_model=List[schemas.Vehicle])
async def get_vehicles_by_property(
    property_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all vehicles associated with a property.

    - **property_id**: ID of the property
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.vehicle.get_by_property(db, property_id=property_id, skip=skip, limit=limit)

# Retrieve a specific vehicle by license plate
@router.get("/vehicles/{license_plate}", response_model=schemas.Vehicle)
async def read_vehicle(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific vehicle by license plate.

    - **license_plate**: The license plate of the vehicle to retrieve
    """
    vehicle = crud.vehicle.get_by_license_plate(db, license_plate=license_plate)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

# Get available parking spots
@router.get("/parking-spots/available", response_model=List[schemas.ParkingSpot])
async def read_available_parking_spots(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all available parking spots.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.parking_spot.get_available_spots(db, skip=skip, limit=limit)

# Create a valet request
@router.post("/valet-requests", response_model=schemas.ValetRequest)
async def create_valet_request(
    valet_request: schemas.ValetRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new valet request.

    - **valet_request**: The details of the valet request to be created
    """
    return crud.valet_request.create_with_duration(db, obj_in=valet_request)

# Get active valet requests
@router.get("/valet-requests/active", response_model=List[schemas.ValetRequest])
async def read_active_valet_requests(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all active valet requests.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.valet_request.get_active_requests(db, skip=skip, limit=limit)

# Get vehicle history by vehicle ID
@router.get("/vehicles/{vehicle_id}/history", response_model=List[schemas.ParkingSpot])
async def get_vehicle_history(
    vehicle_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve the parking history of a specific vehicle.

    - **vehicle_id**: ID of the vehicle
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    history = crud.parking_event.get_by_vehicle(db, vehicle_id=vehicle_id, skip=skip, limit=limit)
    if not history:
        raise HTTPException(status_code=404, detail="No parking history found for this vehicle.")
    return history

# Register a vehicle
@router.post("/vehicles/register", response_model=schemas.Vehicle)
async def register_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new vehicle.

    - **vehicle**: The details of the vehicle to be registered
    """
    existing_vehicle = crud.vehicle.get_by_license_plate(db, license_plate=vehicle.plate_number)
    if existing_vehicle:
        raise HTTPException(status_code=400, detail="Vehicle with this plate number already exists.")
    new_vehicle = crud.vehicle.create(db, obj_in=vehicle)
    return new_vehicle
