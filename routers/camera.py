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
from fastapi import Header
import backoff
from sqlalchemy.exc import OperationalError
import logging
from fastapi.logger import logger

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/", response_model=camera_schema.Camera)
def create_camera(
    camera: camera_schema.CameraCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)  # Authentication middleware
):
    # Log incoming request data
    logger.info(f"Received camera creation request: {camera.model_dump()}")
    logger.info(f"Authenticated business ID: {business.id}")

    # Validate property_id
    property_exists = db.query(Property).filter(
        Property.id == camera.property_id,
        Property.business_id == business.id
    ).first()
    if not property_exists:
        logger.error(f"Invalid or unauthorized property_id: {camera.property_id}")
        raise HTTPException(status_code=400, detail="Invalid or unauthorized property_id")

    # Validate zone_id
    zone_exists = db.query(Zone).filter(
        Zone.id == camera.zone_id,
        Zone.business_id == business.id
    ).first()
    if not zone_exists:
        logger.error(f"Invalid or unauthorized zone_id: {camera.zone_id}")
        raise HTTPException(status_code=400, detail="Invalid or unauthorized zone_id")

    # Log camera capabilities serialization
    capabilities_serialized = json.dumps(camera.capabilities) if camera.capabilities else None
    logger.info(f"Serialized capabilities: {capabilities_serialized}")

    # Serialize capabilities field and assign business_id
    db_camera = camera_model.Camera(
        camera_id=camera.camera_id,
        rtsp_url=camera.rtsp_url,
        status=camera.status,
        property_id=camera.property_id,  # Required field
        zone_id=camera.zone_id,          # Required field
        capabilities=capabilities_serialized,
        name=camera.name,
        location=camera.location,
        direction=camera.direction,
        coverage_area=camera.coverage_area,
        business_id=business.id,         # Assign authenticated business ID
    )

    try:
        db.add(db_camera)
        db.commit()
        db.refresh(db_camera)
        db_camera.capabilities = json.loads(db_camera.capabilities) if db_camera.capabilities else []
        logger.info(f"Successfully created camera: {db_camera}")
        return db_camera
    except Exception as e:
        logger.exception("Error occurred while creating the camera")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{camera_id}", response_model=camera_schema.Camera)
def read_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Authentication middleware
    vt_platform_id: str = Header(..., alias="X-VT-Platform-ID"),  # Explicitly include headers
    api_key: str = Header(..., alias="X-VT-API-Key"),
    business_id: str = Header(..., alias="X-VT-Business-ID")
):

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
def read_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)  # Authentication middleware
):
    cameras = db.query(camera_model.Camera).filter(
        camera_model.Camera.business_id == business.id  # Filter by authenticated business
    ).offset(skip).limit(limit).all()

    for camera in cameras:
        camera.capabilities = (
            json.loads(camera.capabilities) if camera.capabilities else []
        )
    return cameras


@router.put("/{id}", response_model=camera_schema.Camera)
def update_camera(
    id: str,
    camera: camera_schema.CameraCreate,  # CameraCreate now has required fields
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    # Retrieve the camera to be updated
    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.id == id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Validate property_id
    property_exists = db.query(Property).filter(
        Property.id == camera.property_id,
        Property.business_id == business.id
    ).first()
    if not property_exists:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized property_id")

    # Validate zone_id
    zone_exists = db.query(Zone).filter(
        Zone.id == camera.zone_id,
        Zone.business_id == business.id
    ).first()
    if not zone_exists:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized zone_id")

    # Update the fields in the database object
    for key, value in camera.model_dump(exclude_unset=True).items():
        if key == "capabilities" and value is not None:
            # Serialize capabilities field
            setattr(db_camera, key, json.dumps(value))
        else:
            setattr(db_camera, key, value)

    try:
        # Commit changes to the database
        db.commit()
        db.refresh(db_camera)

        # Deserialize capabilities before returning the response
        db_camera.capabilities = (
            json.loads(db_camera.capabilities) if db_camera.capabilities else []
        )
        return db_camera
    except Exception as e:
        # Handle exceptions and rollback transaction
        db.rollback()
        logger.exception("Error occurred while updating the camera")
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{id}")
def delete_camera(
    id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),
):
    @backoff.on_exception(
        backoff.expo,
        OperationalError,
        max_tries=5,
        giveup=lambda e: "database is locked" not in str(e)
    )
    def delete_operation():
        db.begin_nested()
        try:
            db_camera = db.query(camera_model.Camera).filter(
                camera_model.Camera.id == id,
                camera_model.Camera.business_id == business.id,
            ).with_for_update().first()

            if not db_camera:
                raise HTTPException(status_code=404, detail="Camera not found")

            db.delete(db_camera)
            db.commit()
            return {"message": f"Camera {id} has been successfully deleted"}
        except Exception as e:
            db.rollback()
            raise e

    try:
        return delete_operation()
    except OperationalError as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please try again."
        )
