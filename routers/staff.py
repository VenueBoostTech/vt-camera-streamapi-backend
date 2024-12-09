from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
import crud
import schemas as schemas

router = APIRouter()

@router.get("/work-activity/{staff_id}", response_model=List[schemas.WorkSession])
async def get_work_activity(
    staff_id: int,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve work activity for a specific staff member.
    
    - **staff_id**: The ID of the staff member
    - **start_date**: Optional. Filter activities starting from this date
    - **end_date**: Optional. Filter activities up to this date
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    work_activity = crud.staff.get_work_activity(db, staff_id, start_date, end_date, skip, limit)
    if not work_activity:
        raise HTTPException(status_code=404, detail="Work activity not found")
    return work_activity

@router.get("/working-sessions", response_model=List[schemas.WorkSession])
async def get_working_sessions(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve all working sessions.
    
    - **start_date**: Optional. Filter sessions starting from this date
    - **end_date**: Optional. Filter sessions up to this date
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    return crud.staff.get_working_sessions(db, start_date, end_date, skip, limit)

@router.post("/break-monitoring", response_model=schemas.Break)
async def monitor_breaks(
    break_data: schemas.BreakCreate,
    db: Session = Depends(get_db)
):
    """
    Record a new break for a staff member.
    
    - **break_data**: The details of the break to be recorded
    """
    try:
        return crud.staff.monitor_breaks(db, break_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))