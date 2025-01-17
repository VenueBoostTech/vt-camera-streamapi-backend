from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.business import Business
import os
from dotenv import load_dotenv

load_dotenv()

SUPERADMIN_API_KEY = os.environ.get("SUPERADMIN_API_KEY")

async def verify_business_auth(
    db: Session = Depends(get_db),
    vt_platform_id: str = Header(..., alias="X-VT-Platform-ID"),
    api_key: str = Header(..., alias="X-VT-API-Key"),
    business_id: str = Header(..., alias="X-VT-Business-ID")
):
    business = db.query(Business).filter(
        Business.vt_platform_id == vt_platform_id,
        Business.api_key == api_key,
        Business.id == business_id,
        Business.is_active == True,
    ).first()

    if not business:
        raise HTTPException(status_code=401, detail="Invalid or unauthorized business")
    return business

async def verify_superadmin_api_key(
    superadmin_api_key: str = Header(..., alias="X-VT-SUPERADMIN-API-KEY")
):
    if superadmin_api_key and superadmin_api_key != SUPERADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid SUPERADMIN API key")
