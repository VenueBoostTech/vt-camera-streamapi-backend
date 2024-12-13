from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from models.securityEvent import SecurityEvent
from schemas.securityEvent import SecurityEventCreate


class SecurityEventCRUD:
    def create(self, db: Session, obj_in: SecurityEventCreate) -> SecurityEvent:
        db_event = SecurityEvent(**obj_in.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    def get(self, db: Session, id: UUID) -> Optional[SecurityEvent]:
        return db.query(SecurityEvent).filter(SecurityEvent.id == str(id)).first()

    def get_by_property(self, db: Session, property_id: UUID) -> List[SecurityEvent]:
        return db.query(SecurityEvent).filter(SecurityEvent.property_id == str(property_id)).all()

    def update(self, db: Session, id: UUID, obj_in: SecurityEventCreate) -> Optional[SecurityEvent]:
        db_event = self.get(db, id=id)
        if not db_event:
            return None
        for field, value in obj_in.dict().items():
            setattr(db_event, field, value)
        db.commit()
        db.refresh(db_event)
        return db_event


security_event_crud = SecurityEventCRUD()
