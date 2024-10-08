from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import entry_log, exit_log
from datetime import datetime

router = APIRouter()

@router.get("/people-count")
async def people_count(start_time: str, end_time: str, camera_id: Optional[str] = None, db: Session = Depends(get_db)):
    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    entry_query = db.query(entry_log.EntryLog).filter(
        entry_log.EntryLog.timestamp.between(start, end)
    )
    exit_query = db.query(exit_log.ExitLog).filter(
        exit_log.ExitLog.timestamp.between(start, end)
    )
    
    if camera_id:
        entry_query = entry_query.filter(entry_log.EntryLog.camera_id == camera_id)
        exit_query = exit_query.filter(exit_log.ExitLog.camera_id == camera_id)
    
    entry_count = entry_query.count()
    exit_count = exit_query.count()
    
    return {
        "camera_id": camera_id,
        "total_entry_count": entry_count,
        "total_exit_count": exit_count,
    }

# Add more analytics endpoints as needed