from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import smoking_detection as smoking_model
from ..schemas import smoking_detection as smoking_schema

router = APIRouter()

@router.post("/", response_model=smoking_schema.SmokingDetection)
def create_smoking_detection(detection: smoking_schema.SmokingDetectionCreate, db: Session = Depends(get_db)):
    db_detection = smoking_model.SmokingDetection(**detection.dict())
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

@router.get("/", response_model=List[smoking_schema.SmokingDetection])
def read_smoking_detections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    detections = db.query(smoking_model.SmokingDetection).offset(skip).limit(limit).all()
    return detections