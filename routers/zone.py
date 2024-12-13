from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.zone import Zone
from schemas.zone import ZoneCreate, ZoneResponse

router = APIRouter()

@router.post("/properties/{property_id}/zones", response_model=ZoneResponse)
def create_zone(property_id: str, zone: ZoneCreate, db: Session = Depends(get_db)):
    db_zone = Zone(
        property_id=property_id,
        name=zone.name,
        type=zone.type,
        polygon=zone.polygon,
        rules=zone.rules,
        settings=zone.settings,
        active=zone.active
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.get("/properties/{property_id}/zones", response_model=List[ZoneResponse])
def read_zones(property_id: str, db: Session = Depends(get_db)):
    zones = db.query(Zone).filter(Zone.property_id == property_id).all()
    return zones

@router.put("/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: str, zone: ZoneCreate, db: Session = Depends(get_db)):
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    for key, value in zone.dict().items():
        setattr(db_zone, key, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.delete("/zones/{zone_id}")
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted successfully"}
