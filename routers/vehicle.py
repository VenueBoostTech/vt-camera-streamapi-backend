from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import crud
import schemas as schemas

router = APIRouter()

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

@router.post("/valet-requests", response_model=schemas.ValetRequest)
async def create_valet_request(
    valet_request: schemas.ValetRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new valet request.

    - **valet_request**: The details of the valet request to be created
    """
    return crud.valet_request.create(db, obj_in=valet_request)

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