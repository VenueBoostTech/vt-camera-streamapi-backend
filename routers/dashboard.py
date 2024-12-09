# app/api/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
import crud as crud
import schemas as schemas

router = APIRouter()

@router.get("/summary", response_model=schemas.dashboard.MonitoringSummary)
async def get_monitoring_summary(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date")
):
    """
    Retrieve a summary of monitoring data.
    
    - **start_date**: Optional. Filter summary data starting from this date
    - **end_date**: Optional. Filter summary data up to this date
    """
    try:
        return crud.get_monitoring_summary(db, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))