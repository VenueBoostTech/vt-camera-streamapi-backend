from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import parkingEvent as schemas
from crud.parkingEvent import parking_event

router = APIRouter()

@router.get("/properties/{property_id}/parking/status", response_model=List[schemas.ParkingEvent])
def get_parking_status(
    property_id: str, 
    db: Session = Depends(get_db)
):
    """
    Get parking status for a property.
    """
    status = parking_event.get_parking_status_by_property(db, property_id=property_id)
    if not status:
        raise HTTPException(status_code=404, detail="No parking status found for the property")
    return status


@router.get("/zones/{zone_id}/parking/analytics", response_model=List[schemas.ParkingEvent])
def get_parking_analytics(
    zone_id: str, 
    db: Session = Depends(get_db)
):
    """
    Get parking analytics for a specific zone.
    """
    analytics = parking_event.get_parking_analytics_by_zone(db, zone_id=zone_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="No parking analytics found for the zone")
    return analytics


@router.get("/properties/{property_id}/parking/violations", response_model=List[schemas.ParkingEvent])
def get_parking_violations(
    property_id: str, 
    db: Session = Depends(get_db)
):
    """
    Get parking violations for a property.
    """
    violations = parking_event.get_parking_violations_by_property(db, property_id=property_id)
    if not violations:
        raise HTTPException(status_code=404, detail="No parking violations found for the property")
    return violations
