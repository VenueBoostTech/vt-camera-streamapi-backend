from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from models.incident import Incident
from schemas.incident import IncidentCreate, IncidentUpdate


class IncidentCRUD:
    def create(self, db: Session, obj_in: IncidentCreate) -> Incident:
        # Convert related_events UUIDs to strings
        data = obj_in.model_dump()
        if "related_events" in data and data["related_events"]:
            data["related_events"] = [str(event) for event in data["related_events"]]
        data["property_id"] = str(data["property_id"])

        db_incident = Incident(**data)
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        return db_incident

    def get(self, db: Session, id: UUID) -> Optional[Incident]:
        return db.query(Incident).filter(Incident.id == str(id)).first()

    def get_by_property(self, db: Session, property_id: UUID) -> List[Incident]:
        return db.query(Incident).filter(Incident.property_id == str(property_id)).all()

    def update(self, db: Session, id: UUID, obj_in: IncidentUpdate) -> Optional[Incident]:
        db_incident = self.get(db, id=id)
        if not db_incident:
            return None
        for field, value in obj_in.dict().items():
            setattr(db_incident, field, value)
        db.commit()
        db.refresh(db_incident)
        return db_incident


incident_crud = IncidentCRUD()
