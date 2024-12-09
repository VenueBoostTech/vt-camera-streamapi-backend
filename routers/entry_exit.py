from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import entry_log as entry_model, exit_log as exit_model
from schemas import entry_log as entry_schema, exit_log as exit_schema

router = APIRouter()

@router.post("/entrylog/", response_model=entry_schema.EntryLog)
def create_entry_log(entry: entry_schema.EntryLogCreate, db: Session = Depends(get_db)):
    db_entry = entry_model.EntryLog(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.get("/entrylog/", response_model=List[entry_schema.EntryLog])
def read_entry_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    entries = db.query(entry_model.EntryLog).offset(skip).limit(limit).all()
    return entries

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