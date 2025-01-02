from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.business import Business as BusinessModel
from schemas.business import BusinessSchema, BusinessUpdateSchema
from utils.auth_middleware import verify_superadmin_api_key
import uuid

router = APIRouter()

@router.get("/", response_model=List[BusinessSchema])
def read_businesses_as_superadmin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    superadmin_check: None = Depends(verify_superadmin_api_key),
):

    businesses = db.query(BusinessModel).offset(skip).limit(limit).all()
    return businesses

@router.post("/", response_model=BusinessSchema)
def create_business(
    business: BusinessSchema,
    db: Session = Depends(get_db),
    superadmin_check: None = Depends(verify_superadmin_api_key),
):
    """
    Create a new business.
    """
    # Check if the vt_platform_id already exists
    existing_business = db.query(BusinessModel).filter(BusinessModel.vt_platform_id == business.vt_platform_id).first()
    if existing_business:
        raise HTTPException(status_code=400, detail="Business with this vt_platform_id already exists")

    # Create new business
    new_business = BusinessModel(
        id=str(uuid.uuid4()),
        name=business.name,
        vt_platform_id=business.vt_platform_id,
        api_key=business.api_key,
        is_active=True,
        is_local_test=business.is_local_test,
        is_prod_test=business.is_prod_test,
    )

    db.add(new_business)
    db.commit()
    db.refresh(new_business)

    return new_business

@router.get("/{business_id}", response_model=BusinessSchema)
def read_business(
    business_id: str,
    db: Session = Depends(get_db),
    superadmin_check: None = Depends(verify_superadmin_api_key),
):
    """
    Retrieve a single business by its ID.
    """
    business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@router.get("/by-vt-platform-id/{vt_platform_id}", response_model=dict)
def get_business_id_by_vt_platform_id(
    vt_platform_id: str,
    db: Session = Depends(get_db),
    superadmin_check: None = Depends(verify_superadmin_api_key),
):
    business = db.query(BusinessModel).filter(BusinessModel.vt_platform_id == vt_platform_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business with this vt_platform_id not found")
    return {"business_id": business.id}

@router.put("/{business_id}", response_model=BusinessSchema)
def update_business(
    business_id: str,
    business_update: BusinessUpdateSchema,  # Use the partial update schema
    db: Session = Depends(get_db),
    superadmin_check: None = Depends(verify_superadmin_api_key),  # Superadmin auth
):
    business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Update only provided fields
    update_data = business_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)

    db.commit()
    db.refresh(business)

    return business