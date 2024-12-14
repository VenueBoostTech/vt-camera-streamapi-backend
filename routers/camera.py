from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import camera as camera_model
from schemas import camera as camera_schema
from models.property import Property
from models.zone import Zone

router = APIRouter()

@router.post("/", response_model=camera_schema.Camera)
def create_camera(
    camera: camera_schema.CameraCreate, 
    db: Session = Depends(get_db)
):
    # Validate property_id if provided
    if camera.property_id:
        property_exists = db.query(Property).filter(Property.id == camera.property_id).first()
        if not property_exists:
            raise HTTPException(status_code=400, detail="Invalid property_id")

    # Validate zone_id if provided
    if camera.zone_id:
        zone_exists = db.query(Zone).filter(Zone.id == camera.zone_id).first()
        if not zone_exists:
            raise HTTPException(status_code=400, detail="Invalid zone_id")

    # Create camera
    db_camera = camera_model.Camera(**camera.dict())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera


@router.get("/", response_model=List[camera_schema.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cameras = db.query(camera_model.Camera).offset(skip).limit(limit).all()
    return cameras


@router.get("/{camera_id}", response_model=camera_schema.Camera)
def read_camera(camera_id: str, db: Session = Depends(get_db)):
    db_camera = db.query(camera_model.Camera).filter(camera_model.Camera.camera_id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera


@router.put("/{camera_id}", response_model=camera_schema.Camera)
def update_camera(
    camera_id: str,
    camera: camera_schema.CameraCreate,  # Use CameraUpdate schema for partial updates
    db: Session = Depends(get_db)
):
    # Retrieve the camera to update
    db_camera = db.query(camera_model.Camera).filter(camera_model.Camera.camera_id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Validate property_id if provided
    if camera.property_id:
        property_exists = db.query(Property).filter(Property.id == camera.property_id).first()
        if not property_exists:
            raise HTTPException(status_code=400, detail="Invalid property_id")

    # Validate zone_id if provided
    if camera.zone_id:
        zone_exists = db.query(Zone).filter(Zone.id == camera.zone_id).first()
        if not zone_exists:
            raise HTTPException(status_code=400, detail="Invalid zone_id")

    # Update camera fields
    for key, value in camera.dict(exclude_unset=True).items():  # Exclude unset fields
        setattr(db_camera, key, value)
    
    db.commit()
    db.refresh(db_camera)
    return db_camera


@router.delete("/{camera_id}", response_model=camera_schema.Camera)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    db_camera = db.query(camera_model.Camera).filter(camera_model.Camera.camera_id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(db_camera)
    db.commit()
    return db_camera
