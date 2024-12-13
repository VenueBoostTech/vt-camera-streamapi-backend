from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas.behavior import Behavior, BehaviorCreate
from crud.behavior import behavior
from database import get_db

router = APIRouter()

@router.get("/properties/{property_id}/behaviors", response_model=List[Behavior])
def get_behaviors_by_property(property_id: str, db: Session = Depends(get_db)):
    behaviors = behavior.get_behaviors_by_property(db, property_id=property_id)
    return behaviors

@router.get("/zones/{zone_id}/behaviors", response_model=List[Behavior])
def get_behaviors_by_zone(zone_id: str, db: Session = Depends(get_db)):
    behaviors = behavior.get_behaviors_by_zone(db, zone_id=zone_id)
    return behaviors

@router.post("/behaviors/analyze", response_model=List[Behavior])
def analyze_behavior(
    property_id: Optional[str] = None, 
    zone_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    behaviors = behavior.analyze_behavior(db, property_id=property_id, zone_id=zone_id)
    return behaviors
