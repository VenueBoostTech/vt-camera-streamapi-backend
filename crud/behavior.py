from sqlalchemy.orm import Session
from models.behavior import Behavior
from schemas.behavior import BehaviorCreate
from typing import Optional


class CRUDBahavior:
    def create(self, db: Session, behavior_data: BehaviorCreate):
        db_behavior = Behavior(**behavior_data.dict())
        db.add(db_behavior)
        db.commit()
        db.refresh(db_behavior)
        return db_behavior

    def get_behaviors_by_property(self, db: Session, property_id: str):
        return db.query(Behavior).filter(Behavior.property_id == property_id).all()

    def get_behaviors_by_zone(self, db: Session, zone_id: str):
        return db.query(Behavior).filter(Behavior.zone_id == zone_id).all()

    def analyze_behavior(self, db: Session, property_id: Optional[str], zone_id: Optional[str]):
        query = db.query(Behavior)
        if property_id:
            query = query.filter(Behavior.property_id == property_id)
        if zone_id:
            query = query.filter(Behavior.zone_id == zone_id)
        return query.all()

behavior = CRUDBahavior()
