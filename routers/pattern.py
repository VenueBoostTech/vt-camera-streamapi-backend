from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas.pattern import Pattern, PatternCreate
from crud.pattern import pattern
from database import get_db

router = APIRouter()

@router.get("/properties/{property_id}/patterns", response_model=List[Pattern])
def get_patterns_by_property(property_id: str, db: Session = Depends(get_db)):
    patterns = pattern.get_patterns_by_property(db, property_id=property_id)
    return patterns

@router.get("/zones/{zone_id}/patterns", response_model=List[Pattern])
def get_patterns_by_zone(zone_id: str, db: Session = Depends(get_db)):
    patterns = pattern.get_patterns_by_zone(db, zone_id=zone_id)
    return patterns

@router.post("/patterns/analyze", response_model=List[Pattern])
def analyze_patterns(
    property_id: Optional[str] = None, 
    zone_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    patterns = pattern.analyze_patterns(db, property_id=property_id, zone_id=zone_id)
    return patterns
