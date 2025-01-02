from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.business import Business as BusinessModel
from schemas.business import BusinessSchema
from utils.auth_middleware import verify_superadmin_api_key

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
