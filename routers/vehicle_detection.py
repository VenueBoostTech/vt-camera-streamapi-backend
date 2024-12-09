from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import vehicle_detection as vehicle_model
from schemas import vehicle_detection as vehicle_schema

router = APIRouter()

@router.post("/", response_model=vehicle_schema.VehicleDetection)
def create_vehicle_detection(detection: vehicle_schema.VehicleDetectionCreate, db: Session = Depends(get_db)):
    db_detection = vehicle_model.VehicleDetection(**detection.dict())
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

@router.get("/", response_model=List[vehicle_schema.VehicleDetection])
def read_vehicle_detections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    detections = db.query(vehicle_model.VehicleDetection).offset(skip).limit(limit).all()
    return detections