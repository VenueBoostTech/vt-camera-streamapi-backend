from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from schemas.incident import Incident, IncidentCreate, IncidentUpdate
from crud.incident import incident_crud
from database import get_db

router = APIRouter()

# POST /api/v1/incidents
@router.post("/incidents", response_model=Incident)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    new_incident = incident_crud.create(db, obj_in=incident)
    return new_incident


# GET /api/v1/properties/{id}/incidents
@router.get("/properties/{id}/incidents", response_model=List[Incident])
def get_incidents_by_property(id: UUID, db: Session = Depends(get_db)):
    incidents = incident_crud.get_by_property(db, property_id=id)
    if not incidents:
        raise HTTPException(status_code=404, detail="No incidents found for this property")
    return incidents


# PUT /api/v1/incidents/{id}
@router.put("/incidents/{id}", response_model=Incident)
def update_incident(id: UUID, incident: IncidentUpdate, db: Session = Depends(get_db)):
    updated_incident = incident_crud.update(db, id=id, obj_in=incident)
    if not updated_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated_incident


# GET /api/v1/incidents/{id}/events
@router.get("/incidents/{id}/events", response_model=List[UUID])
def get_incident_events(id: UUID, db: Session = Depends(get_db)):
    incident = incident_crud.get(db, id=id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.related_events if incident.related_events else []
