from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import camera as camera_model
from schemas import camera as camera_schema

router = APIRouter()

@router.post("/", response_model=camera_schema.Camera)
def create_camera(camera: camera_schema.CameraCreate, db: Session = Depends(get_db)):
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
def update_camera(camera_id: str, camera: camera_schema.CameraCreate, db: Session = Depends(get_db)):
    db_camera = db.query(camera_model.Camera).filter(camera_model.Camera.camera_id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    for key, value in camera.dict().items():
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