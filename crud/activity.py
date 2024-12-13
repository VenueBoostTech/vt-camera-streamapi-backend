from sqlalchemy.orm import Session
from models.staff import Activity
from schemas.staff import ActivityCreate
from typing import Optional

# Behavior 
class CRUDAcitivity:
    def create(self, db: Session, activity_data: ActivityCreate):
        db_activity = Activity(**activity_data.dict())
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        return db_activity

    def get_activities_by_property(self, db: Session, property_id: str):
        return db.query(Activity).filter(Activity.property_id == property_id).all()

    def get_activities_by_zone(self, db: Session, zone_id: str):
        return db.query(Activity).filter(Activity.zone_id == zone_id).all()

    def analyze_activity(self, db: Session, property_id: Optional[str], zone_id: Optional[str]):
        # Example: Add analysis logic based on your requirements
        query = db.query(Activity)
        if property_id:
            query = query.filter(Activity.property_id == property_id)
        if zone_id:
            query = query.filter(Activity.zone_id == zone_id)
        return query.all()

activity = CRUDAcitivity()
