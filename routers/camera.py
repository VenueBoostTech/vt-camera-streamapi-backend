from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import camera as camera_model
from schemas import camera as camera_schema
from models.property import Property
from models.zone import Zone
import json
from models.business import Business
from utils.auth_middleware import verify_business_auth

router = APIRouter()


@router.post("/", response_model=camera_schema.Camera)
def create_camera(
    camera: camera_schema.CameraCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)  # Authentication middleware
):
    """
    Create a new camera with property and zone validation and business ownership check.
    """
    # Validate property_id if provided
    if camera.property_id:
        property_exists = db.query(Property).filter(
            Property.id == camera.property_id, Property.business_id == business.id
        ).first()
        if not property_exists:
            raise HTTPException(status_code=400, detail="Invalid or unauthorized property_id")

    # Validate zone_id if provided
    if camera.zone_id:
        zone_exists = db.query(Zone).filter(
            Zone.id == camera.zone_id, Zone.business_id == business.id
        ).first()
        if not zone_exists:
            raise HTTPException(status_code=400, detail="Invalid or unauthorized zone_id")

    # Serialize capabilities field and assign business_id
    db_camera = camera_model.Camera(
        camera_id=camera.camera_id,
        rtsp_url=camera.rtsp_url,
        status=camera.status,
        property_id=camera.property_id,
        zone_id=camera.zone_id,
        capabilities=json.dumps(camera.capabilities) if camera.capabilities else None,
        name=camera.name,
        location=camera.location,
        direction=camera.direction,
        coverage_area=camera.coverage_area,
        business_id=business.id,  # Assign authenticated business ID
    )

    try:
        db.add(db_camera)
        db.commit()
        db.refresh(db_camera)
        db_camera.capabilities = json.loads(db_camera.capabilities) if db_camera.capabilities else []
        return db_camera
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Header

@router.get("/{camera_id}", response_model=camera_schema.Camera)
def read_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Authentication middleware
    vt_platform_id: str = Header(..., alias="X-VT-Platform-ID"),  # Explicitly include headers
    api_key: str = Header(..., alias="X-VT-API-Key"),
    business_id: str = Header(..., alias="X-VT-Business-ID")
):
    """
    Retrieve a camera by ID and ensure it belongs to the authenticated business.
    """
    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.camera_id == camera_id,
        camera_model.Camera.business_id == business.id  # Ensure it belongs to the business
    ).first()

    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Deserialize capabilities field
    db_camera.capabilities = json.loads(db_camera.capabilities) if db_camera.capabilities else []
    return db_camera


@router.get("/", response_model=List[camera_schema.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cameras = db.query(camera_model.Camera).offset(skip).limit(limit).all()
    for camera in cameras:
        camera.capabilities = (
            json.loads(camera.capabilities) if camera.capabilities else []
        )
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
