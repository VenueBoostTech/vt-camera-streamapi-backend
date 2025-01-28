from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List, Optional
from datetime import datetime
from schemas.footpath import FootpathAnalytics, FootpathPattern
from crud.footpath import footpath_crud

router = APIRouter()

@router.post("/vt/api/v1/footpath/analytics/{zone_id}", response_model=FootpathAnalytics)
def create_footpath_analytics(
    zone_id: str,
    analytics_data: FootpathAnalytics,
    db: Session = Depends(get_db)
):
    """Create new footpath analytics for a zone"""
    return footpath_crud.create_analytics(
        db=db,
        zone_id=zone_id,
        analytics_data=analytics_data.dict()
    )

@router.get("/vt/api/v1/footpath/analytics/{zone_id}", response_model=List[FootpathAnalytics])
def get_zone_analytics(
    zone_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get footpath analytics for a specific zone"""
    return footpath_crud.get_zone_analytics(
        db=db,
        zone_id=zone_id,
        start_time=start_time,
        end_time=end_time
    )

@router.get("/vt/api/v1/footpath/patterns/{zone_id}", response_model=List[FootpathPattern])
def get_zone_patterns(
    zone_id: str,
    min_frequency: int = 2,
    db: Session = Depends(get_db)
):
    """Get footpath patterns for a zone"""
    return footpath_crud.get_patterns(
        db=db,
        zone_id=zone_id,
        min_frequency=min_frequency
    )

@router.post("/vt/api/v1/footpath/patterns/{zone_id}", response_model=FootpathPattern)
def create_pattern(
    zone_id: str,
    pattern_data: FootpathPattern,
    db: Session = Depends(get_db)
):
    """Create new footpath pattern"""
    return footpath_crud.create_pattern(
        db=db,
        zone_id=zone_id,
        pattern_data=pattern_data.dict()
    )
