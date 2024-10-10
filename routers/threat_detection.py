from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import threat_detection as threat_model
from schemas import threat_detection as threat_schema

router = APIRouter()

@router.post("/", response_model=threat_schema.ThreatDetection)
def create_threat_detection(detection: threat_schema.ThreatDetectionCreate, db: Session = Depends(get_db)):
    db_detection = threat_model.ThreatDetection(**detection.dict())
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

@router.get("/", response_model=List[threat_schema.ThreatDetection])
def read_threat_detections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    detections = db.query(threat_model.ThreatDetection).offset(skip).limit(limit).all()
    return detections