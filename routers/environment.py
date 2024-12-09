from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import schemas as schemas
import crud

router = APIRouter()

@router.post("/smoke-detection", response_model=schemas.SmokeDetection)
async def create_smoke_detection(
    smoke: schemas.SmokeDetectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new smoke detection entry.

    - **smoke**: The details of the smoke detection to be created
    """
    return crud.smoke_detection.create(db, obj_in=smoke)

@router.get("/smoke-detection/active-alarms", response_model=List[schemas.SmokeDetection])
async def read_active_smoke_alarms(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all active smoke alarms.

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.smoke_detection.get_active_alarms(db, skip=skip, limit=limit)