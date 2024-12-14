from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import property as property_model
from schemas import property as property_schema
from uuid import UUID
import json
from datetime import datetime

router = APIRouter()

@router.post("/properties/", response_model=property_schema.ExtendedPropertyResponse)
def create_property(property: property_schema.PropertyCreate, db: Session = Depends(get_db)):
    # Create property
    db_property = property_model.Property(
        name=property.name,
        type=property.type,
        address=property.address,
        settings=property.settings,
        created_at=property.created_at,
        updated_at=property.updated_at
    )
    db.add(db_property)
    db.flush()  # Flush to get the property ID

    # Create associated buildings
    for building_data in property.buildings:
        db_building = property_model.Building(
            property_id=db_property.id,
            name=building_data.name,
            type=building_data.type,
            sub_address=building_data.sub_address,
            settings=building_data.settings
        )
        db.add(db_building)

    db.commit()
    db.refresh(db_property)
    return db_property

@router.get("/properties/", response_model=List[property_schema.PropertyResponse])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    properties = db.query(property_model.Property).offset(skip).limit(limit).all()
    
    # Ensure settings is always a dict
    for prop in properties:
        if prop.settings is None:
            prop.settings = {}
        elif isinstance(prop.settings, str):
            try:
                prop.settings = json.loads(prop.settings)
            except json.JSONDecodeError:
                prop.settings = {}
    
    return properties

@router.get("/properties/{property_id}", response_model=property_schema.ExtendedPropertyResponse)
def read_property(property_id: str, db: Session = Depends(get_db)):
    db_property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property

@router.put("/properties/{property_id}", response_model=property_schema.ExtendedPropertyResponse)
def update_property(
    property_id: str,
    property_update: property_schema.PropertyCreate,
    db: Session = Depends(get_db)
):
    db_property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update property fields
    for key, value in property_update.model_dump(exclude={'buildings'}).items():
        setattr(db_property, key, value)
    
    # Update buildings
    if property_update.buildings:
        # Remove existing buildings not in the update
        existing_building_names = {building.name for building in property_update.buildings}
        for building in db_property.buildings:
            if building.name not in existing_building_names:
                db.delete(building)
        
        # Update or create buildings
        for building_data in property_update.buildings:
            db_building = next(
                (b for b in db_property.buildings if b.name == building_data.name),
                None
            )
            if db_building:
                # Update existing building
                for key, value in building_data.model_dump().items():
                    if key != 'property_id':
                        setattr(db_building, key, value)
            else:
                # Create new building
                db_building = property_model.Building(
                    property_id=property_id,
                    name=building_data.name,
                    type=building_data.type,
                    sub_address=building_data.sub_address,
                    settings=building_data.settings
                )
                db.add(db_building)

    db_property.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_property)
    return db_property

@router.delete("/properties/{property_id}")
def delete_property(property_id: str, db: Session = Depends(get_db)):
    db_property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(db_property)
    db.commit()
    return {"message": "Property deleted successfully"}

# Building routes
@router.post("/buildings/", response_model=property_schema.BuildingResponse)
def create_building(building: property_schema.BuildingCreate, db: Session = Depends(get_db)):
    # Verify property exists first
    property = db.query(property_model.Property).filter(property_model.Property.id == building.property_id).first()
    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"Property with ID {building.property_id} not found"
        )
    
    # Create building
    db_building = property_model.Building(
        property_id=building.property_id,
        name=building.name,
        type=building.type,
        sub_address=building.sub_address,
        settings=building.settings
    )
    
    db.add(db_building)
    try:
        db.commit()
        db.refresh(db_building)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return db_building


@router.get("/buildings/{building_id}", response_model=property_schema.ExtendedBuildingResponse)
def read_building(building_id: str, db: Session = Depends(get_db)):
    db_building = db.query(property_model.Building).filter(property_model.Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building

@router.put("/buildings/{building_id}", response_model=property_schema.BuildingResponse)
def update_building(
    building_id: str,
    building_update: property_schema.BuildingCreate,
    db: Session = Depends(get_db)
):
    db_building = db.query(property_model.Building).filter(property_model.Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    
    for key, value in building_update.model_dump().items():
        setattr(db_building, key, value)
    
    db.commit()
    db.refresh(db_building)
    return db_building

@router.delete("/buildings/{building_id}")
def delete_building(building_id: str, db: Session = Depends(get_db)):
    db_building = db.query(property_model.Building).filter(property_model.Building.id == building_id).first()
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    db.delete(db_building)
    db.commit()
    return {"message": "Building deleted successfully"}

# Floor routes
@router.post("/floors/", response_model=property_schema.FloorResponse)
def create_floor(floor: property_schema.FloorCreate, db: Session = Depends(get_db)):
    # Verify building exists
    if not db.query(property_model.Building).filter(property_model.Building.id == floor.building_id).first():
        raise HTTPException(status_code=404, detail="Building not found")
    
    db_floor = property_model.Floor(**floor.model_dump())
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)
    return db_floor

@router.get("/floors/{floor_id}", response_model=property_schema.FloorResponse)
def read_floor(floor_id: str, db: Session = Depends(get_db)):
    db_floor = db.query(property_model.Floor).filter(property_model.Floor.id == floor_id).first()
    if db_floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")
    return db_floor

@router.put("/floors/{floor_id}", response_model=property_schema.FloorResponse)
def update_floor(floor_id: str, floor_update: property_schema.FloorCreate, db: Session = Depends(get_db)):
    db_floor = db.query(property_model.Floor).filter(property_model.Floor.id == floor_id).first()
    if db_floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")
    
    for key, value in floor_update.model_dump().items():
        setattr(db_floor, key, value)
    
    db.commit()
    db.refresh(db_floor)
    return db_floor

@router.delete("/floors/{floor_id}")
def delete_floor(floor_id: str, db: Session = Depends(get_db)):
    db_floor = db.query(property_model.Floor).filter(property_model.Floor.id == floor_id).first()
    if db_floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")
    db.delete(db_floor)
    db.commit()
    return {"message": "Floor deleted successfully"}