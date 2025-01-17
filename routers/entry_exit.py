from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import entry_log as entry_model, exit_log as exit_model
from schemas import entry_log as entry_schema, exit_log as exit_schema
from sqlalchemy.sql import func


router = APIRouter()

@router.post("/entrylog/", response_model=entry_schema.EntryLog)
def create_entry_log(entry: entry_schema.EntryLogCreate, db: Session = Depends(get_db)):
    db_entry = entry_model.EntryLog(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/entrylog/summary/", response_model=List[entry_schema.EntryLogSummary])
def get_entry_log_summary(db: Session = Depends(get_db)):
    # Query to aggregate data grouped by the hour (time)
    summary_query = (
        db.query(
            func.strftime('%H:00', entry_model.EntryLog.timestamp).label("time"),
            func.sum(entry_model.EntryLog.entering).label("entering"),
            func.sum(entry_model.EntryLog.exiting).label("exiting"),
            func.sum(entry_model.EntryLog.in_store).label("inStore"),
        )
        .group_by(func.strftime('%H:00', entry_model.EntryLog.timestamp))
        .all()
    )

    # Convert query result to the desired response format
    summary = [
        {
            "time": result.time,
            "entering": result.entering,
            "exiting": result.exiting,
            "inStore": result.inStore,
        }
        for result in summary_query
    ]

    return summary

@router.post("/exitlog/", response_model=exit_schema.ExitLog)
def create_exit_log(exit: exit_schema.ExitLogCreate, db: Session = Depends(get_db)):
    db_exit = exit_model.ExitLog(**exit.dict())
    db.add(db_exit)
    db.commit()
    db.refresh(db_exit)
    return db_exit

@router.get("/exitlog/", response_model=List[exit_schema.ExitLog])
def read_exit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    exits = db.query(exit_model.ExitLog).offset(skip).limit(limit).all()
    return exits