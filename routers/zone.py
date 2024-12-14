from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneResponse

router = APIRouter()

@router.post("/properties/{property_id}/zones", response_model=ZoneResponse)
def create_zone(property_id: str, zone: ZoneCreate, db: Session = Depends(get_db)):
    # Validate the property_id matches the incoming zone.property_id
    if zone.property_id != property_id:
        raise HTTPException(status_code=400, detail="Mismatched property_id")

    # Create the zone
    db_zone = Zone(
        property_id=property_id,
        building_id=zone.building_id,
        floor_id=zone.floor_id,
        name=zone.name,
        type=zone.type,
        polygon=zone.polygon,
        rules=zone.rules,
        settings=zone.settings,
        active=zone.active,
        access_level=zone.access_level,
        capacity=zone.capacity,
        square_footage=zone.square_footage,
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.get("/properties/{property_id}/zones", response_model=List[ZoneResponse])
def read_zones(property_id: str, db: Session = Depends(get_db)):
    # Fetch all zones for the given property_id
    zones = db.query(Zone).filter(Zone.property_id == property_id).all()
    return zones

@router.get("/zones/{zone_id}", response_model=ZoneResponse)
def read_zone(zone_id: UUID, db: Session = Depends(get_db)):
    # Fetch a single zone by its UUID
    db_zone = db.query(Zone).filter(Zone.id == str(zone_id)).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return db_zone

@router.put("/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: UUID, zone: ZoneCreate, db: Session = Depends(get_db)):
    # Retrieve the zone to update
    db_zone = db.query(Zone).filter(Zone.id == str(zone_id)).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Update fields dynamically
    for key, value in zone.dict(exclude_unset=True).items():
        setattr(db_zone, key, value)

    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.delete("/zones/{zone_id}")
def delete_zone(zone_id: UUID, db: Session = Depends(get_db)):
    # Find the zone to delete
    db_zone = db.query(Zone).filter(Zone.id == str(zone_id)).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted successfully"}
