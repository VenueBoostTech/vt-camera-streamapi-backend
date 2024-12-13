from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from schemas.securityEvent import SecurityEvent, SecurityEventCreate
from crud.securityEvent import security_event_crud
from database import get_db

router = APIRouter()

# POST /api/v1/events
@router.post("/events", response_model=SecurityEvent)
def create_event(event: SecurityEventCreate, db: Session = Depends(get_db)):
    new_event = security_event_crud.create(db, obj_in=event)
    return new_event


# GET /api/v1/properties/{id}/events
@router.get("/properties/{id}/events", response_model=List[SecurityEvent])
def get_events_by_property(id: UUID, db: Session = Depends(get_db)):
    events = security_event_crud.get_by_property(db, property_id=id)
    if not events:
        raise HTTPException(status_code=404, detail="No events found for this property")
    return events


# PUT /api/v1/events/{id}
@router.put("/events/{id}", response_model=SecurityEvent)
def update_event(id: UUID, event: SecurityEventCreate, db: Session = Depends(get_db)):
    updated_event = security_event_crud.update(db, id=id, obj_in=event)
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated_event


# GET /api/v1/events/{id}/evidence
@router.get("/events/{id}/evidence", response_model=List[dict])
def get_event_evidence(id: UUID, db: Session = Depends(get_db)):
    event = security_event_crud.get(db, id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.evidence if event.evidence else []
