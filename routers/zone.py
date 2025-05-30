from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneResponse
import json
from models.business import Business
from utils.auth_middleware import verify_business_auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/properties/{property_id}/zones", response_model=ZoneResponse)
def create_zone(
    property_id: str,
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Auth middleware
):
    if zone.property_id != property_id:
        raise HTTPException(status_code=400, detail="Mismatched property_id")

    # Ensure the business ID matches
    db_zone = Zone(
        property_id=property_id,
        building_id=zone.building_id,
        floor_id=zone.floor_id,
        name=zone.name,
        type=zone.type,
        polygon=json.dumps(zone.polygon),
        rules=zone.rules,
        settings=zone.settings,
        active=zone.active,
        access_level=zone.access_level,
        capacity=zone.capacity,
        square_footage=zone.square_footage,
        business_id=business.id,  # Assign authenticated business ID
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.get("/properties/{property_id}/zones", response_model=List[ZoneResponse])
def read_zones(
    property_id: str,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Auth middleware
):
    # Fetch all zones for the given property and business
    zones = db.query(Zone).filter(
        Zone.property_id == property_id,
        Zone.business_id == business.id
    ).all()
    return zones

@router.get("/zones/{zone_id}", response_model=ZoneResponse)
def read_zone(
    zone_id: UUID,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Middleware for business validation
):
    # Fetch a single zone by its UUID and business ID
    db_zone = db.query(Zone).filter(
        Zone.id == str(zone_id),
        Zone.business_id == business.id  # Ensure the zone belongs to the authenticated business
    ).first()

    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return db_zone

@router.put("/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(
    zone_id: UUID,
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Middleware for business validation
):
    # Log the incoming request
    logger.info(f"Incoming PUT request to update zone {zone_id}")
    logger.info(f"Request body: {zone.dict()}")
    logger.info(f"Business ID: {business.id}")

    # Retrieve the zone to update
    db_zone = db.query(Zone).filter(
        Zone.id == str(zone_id),
        Zone.business_id == business.id  # Ensure the zone belongs to the authenticated business
    ).first()

    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Update fields dynamically
    for key, value in zone.model_dump(exclude_unset=True).items():
        logger.info(f"Updating field {key} to {value}")  # Log each update
        setattr(db_zone, key, value)

    db.commit()
    db.refresh(db_zone)
    logger.info(f"Zone {zone_id} successfully updated")

    return db_zone

@router.delete("/zones/{zone_id}")
def delete_zone(
    zone_id: UUID,
    db: Session = Depends(get_db),
    business: Business = Depends(verify_business_auth),  # Middleware for business validation
):
    # Find the zone to delete
    db_zone = db.query(Zone).filter(
        Zone.id == str(zone_id),
        Zone.business_id == business.id  # Ensure the zone belongs to the authenticated business
    ).first()

    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted successfully"}
