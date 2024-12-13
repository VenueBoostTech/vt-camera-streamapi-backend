from sqlalchemy.orm import Session
from models.pattern import Pattern
from schemas.pattern import PatternCreate
from typing import Optional

class CRUDPattern:
    def create(self, db: Session, pattern_data: PatternCreate):
        db_pattern = Pattern(**pattern_data.dict())
        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        return db_pattern

    def get_patterns_by_property(self, db: Session, property_id: str):
        return db.query(Pattern).filter(Pattern.property_id == property_id).all()

    def get_patterns_by_zone(self, db: Session, zone_id: str):
        return db.query(Pattern).filter(Pattern.zone_id == zone_id).all()

    def analyze_patterns(self, db: Session, property_id: Optional[str], zone_id: Optional[str]):
        query = db.query(Pattern)
        if property_id:
            query = query.filter(Pattern.property_id == property_id)
        if zone_id:
            query = query.filter(Pattern.zone_id == zone_id)
        return query.all()

pattern = CRUDPattern()
