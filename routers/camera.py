from fastapi import APIRouter, Depends, HTTPException, Header
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
import backoff
from sqlalchemy.exc import OperationalError
import logging
from fastapi.logger import logger
from services.streaming.stream_manager import stream_manager
from fastapi.responses import JSONResponse

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/", response_model=camera_schema.Camera)
def create_camera(
    camera: camera_schema.CameraCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    logger.info(f"Received camera creation request: {camera.model_dump()}")
    logger.info(f"Authenticated business ID: {business.id}")

    property_exists = db.query(Property).filter(
        Property.id == camera.property_id,
        Property.business_id == business.id
    ).first()
    if not property_exists:
        logger.error(f"Invalid or unauthorized property_id: {camera.property_id}")
        raise HTTPException(status_code=400, detail="Invalid or unauthorized property_id")

    zone_exists = db.query(Zone).filter(
        Zone.id == camera.zone_id,
        Zone.business_id == business.id
    ).first()
    if not zone_exists:
        logger.error(f"Invalid or unauthorized zone_id: {camera.zone_id}")
        raise HTTPException(status_code=400, detail="Invalid or unauthorized zone_id")

    capabilities_serialized = json.dumps(camera.capabilities) if camera.capabilities else None
    logger.info(f"Serialized capabilities: {capabilities_serialized}")

    db_camera = camera_model.Camera(
        camera_id=camera.camera_id,
        rtsp_url=camera.rtsp_url,
        status=camera.status,
        property_id=camera.property_id,
        zone_id=camera.zone_id,
        capabilities=capabilities_serialized,
        name=camera.name,
        location=camera.location,
        direction=camera.direction,
        coverage_area=camera.coverage_area,
        business_id=business.id,
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
    business: Business = Depends(verify_business_auth),
    vt_platform_id: str = Header(..., alias="X-VT-Platform-ID"),
    api_key: str = Header(..., alias="X-VT-API-Key"),
    business_id: str = Header(..., alias="X-VT-Business-ID")
):
    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.camera_id == camera_id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    db_camera.capabilities = json.loads(db_camera.capabilities) if db_camera.capabilities else []
    return db_camera

@router.get("/", response_model=List[camera_schema.Camera])
def read_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    cameras = db.query(camera_model.Camera).offset(skip).limit(limit).all()

    for camera in cameras:
        camera.capabilities = (
            json.loads(camera.capabilities) if camera.capabilities else []
        )
    return cameras

@router.put("/{id}", response_model=camera_schema.Camera)
def update_camera(
    id: str,
    camera: camera_schema.CameraCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.id == id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    property_exists = db.query(Property).filter(
        Property.id == camera.property_id,
        Property.business_id == business.id
    ).first()
    if not property_exists:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized property_id")

    zone_exists = db.query(Zone).filter(
        Zone.id == camera.zone_id,
        Zone.business_id == business.id
    ).first()
    if not zone_exists:
        raise HTTPException(status_code=400, detail="Invalid or unauthorized zone_id")

    for key, value in camera.model_dump(exclude_unset=True).items():
        if key == "capabilities" and value is not None:
            setattr(db_camera, key, json.dumps(value))
        else:
            setattr(db_camera, key, value)

    try:
        db.commit()
        db.refresh(db_camera)
        db_camera.capabilities = (
            json.loads(db_camera.capabilities) if db_camera.capabilities else []
        )
        return db_camera
    except Exception as e:
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

            # Stop any active stream before deleting
            stream_manager.stop_stream(db_camera.camera_id)

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

# New Streaming Endpoints
@router.post("/{camera_id}/stream/start")
async def start_camera_stream(
    camera_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    """Start streaming for a camera"""
    logger.info(f"Starting stream for camera {camera_id}")

    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.camera_id == camera_id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        logger.error(f"Camera {camera_id} not found")
        raise HTTPException(status_code=404, detail="Camera not found")

    if not db_camera.rtsp_url:
        logger.error(f"Camera {camera_id} has no RTSP URL")
        raise HTTPException(status_code=400, detail="Camera has no RTSP URL")

    try:
        success = stream_manager.start_stream(camera_id, db_camera.rtsp_url)
        if not success:
            logger.error(f"Failed to start stream for camera {camera_id}")
            raise HTTPException(status_code=500, detail="Failed to start stream")

        stream_url = stream_manager.get_stream_url(camera_id)
        logger.info(f"Successfully started stream for camera {camera_id}")

        return JSONResponse({
            "status": "started",
            "stream_url": stream_url,
            "camera_id": camera_id
        })

    except Exception as e:
        logger.exception(f"Error starting stream for camera {camera_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{camera_id}/stream/stop")
async def stop_camera_stream(
    camera_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    """Stop streaming for a camera"""
    logger.info(f"Stopping stream for camera {camera_id}")

    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.camera_id == camera_id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        logger.error(f"Camera {camera_id} not found")
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        success = stream_manager.stop_stream(camera_id)
        if not success:
            logger.error(f"Failed to stop stream for camera {camera_id}")
            raise HTTPException(status_code=500, detail="Failed to stop stream")

        logger.info(f"Successfully stopped stream for camera {camera_id}")
        return JSONResponse({"status": "stopped", "camera_id": camera_id})

    except Exception as e:
        logger.exception(f"Error stopping stream for camera {camera_id}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{camera_id}/stream/status")
async def get_stream_status(
    camera_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth)
):
    """Get stream status for a camera"""
    logger.info(f"Getting stream status for camera {camera_id}")

    db_camera = db.query(camera_model.Camera).filter(
        camera_model.Camera.camera_id == camera_id,
        camera_model.Camera.business_id == business.id
    ).first()

    if not db_camera:
        logger.error(f"Camera {camera_id} not found")
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        stream_url = stream_manager.get_stream_url(camera_id)
        status = {
            "is_active": stream_url is not None,
            "stream_url": stream_url,
            "camera_id": camera_id,
            "camera_status": db_camera.status
        }

        logger.info(f"Stream status for camera {camera_id}: {status}")
        return JSONResponse(status)

    except Exception as e:
        logger.exception(f"Error getting stream status for camera {camera_id}")
        raise HTTPException(status_code=500, detail=str(e))