from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import crud
import schemas as schemas

router = APIRouter()

@router.post("/threat-detection", response_model=schemas.ThreatDetection)
async def create_threat_detection(
    threat: schemas.ThreatDetectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new threat detection entry.

    - **threat**: The details of the threat detection to be created
    """
    return crud.threat_detection.create(db, obj_in=threat)

@router.get("/threat-detection/{threat_id}", response_model=schemas.ThreatDetection)
async def read_threat_detection(
    threat_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific threat detection by ID.

    - **threat_id**: The ID of the threat detection to retrieve
    """
    threat = crud.threat_detection.get(db, id=threat_id)
    if threat is None:
        raise HTTPException(status_code=404, detail="Threat detection not found")
    return threat

@router.post("/sleeping-detection", response_model=schemas.SleepingDetection)
async def create_sleeping_detection(
    sleeping: schemas.SleepingDetectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new sleeping detection entry.

    - **sleeping**: The details of the sleeping detection to be created
    """
    return crud.sleeping_detection.create(db, obj_in=sleeping)

@router.get("/sleeping-detection/{staff_id}", response_model=List[schemas.SleepingDetection])
async def read_sleeping_detection(
    staff_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve sleeping detections for a specific staff member.

    - **staff_id**: The ID of the staff member
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.sleeping_detection.get_by_staff(db, staff_id=staff_id, skip=skip, limit=limit)