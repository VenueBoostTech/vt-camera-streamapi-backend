from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.parkingAnalytics import ParkingAnalytics as ParkingAnalyticsSchema
from crud.parkingAnalytics import parking_analytics

router = APIRouter()


@router.get("/properties/{property_id}/vehicle-analytics", response_model=List[ParkingAnalyticsSchema])
def get_vehicle_analytics(
    property_id: str, 
    db: Session = Depends(get_db)
):
    """
    Get vehicle analytics for a property.
    """
    analytics = parking_analytics.get_vehicle_analytics_by_property(db, property_id=property_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="No vehicle analytics found for the property")
    return analytics


@router.get("/zones/{zone_id}/vehicle-patterns", response_model=List[ParkingAnalyticsSchema])
def get_vehicle_patterns(
    zone_id: str, 
    db: Session = Depends(get_db)
):
    """
    Get vehicle patterns for a specific zone.
    """
    patterns = parking_analytics.get_vehicle_patterns_by_zone(db, zone_id=zone_id)
    if not patterns:
        raise HTTPException(status_code=404, detail="No vehicle patterns found for the zone")
    return patterns
