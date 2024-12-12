from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import property as property_model
from schemas import property as property_schema
from uuid import UUID


router = APIRouter()

@router.post("/properties/", response_model=property_schema.PropertyResponse)
def create_property(property: property_schema.PropertyCreate, db: Session = Depends(get_db)):
    db_property = property_model.Property(
        name=property.name,
        type=property.type,
        address=property.address,
        settings=property.settings,
        created_at=property.created_at,
        updated_at=property.updated_at
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


@router.get("/properties/", response_model=List[property_schema.PropertyResponse])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    properties = db.query(property_model.Property).offset(skip).limit(limit).all()
    return properties

@router.get("/properties/{property_id}", response_model=property_schema.PropertyResponse)
def read_property(property_id: str, db: Session = Depends(get_db)):
    db_property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property

@router.put("/properties/{property_id}", response_model=property_schema.PropertyCreate)
def update_property(property_id: str, property: property_schema.PropertyCreate, db: Session = Depends(get_db)):
    db_property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    for key, value in property.model_dump().items():
        setattr(db_property, key, value)
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
