from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
from typing import Optional 

class BusinessSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    vt_platform_id: str
    api_key: Optional[str] = None
    is_active: Optional[bool] = True  # Optional with default value
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))  # Optional with default
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))  # Optional with default
    is_local_test: Optional[bool] = False 
    is_prod_test: Optional[bool] = True 

    class Config:
        orm_mode = True

class BusinessUpdateSchema(BaseModel):
    name: Optional[str] = None
    vt_platform_id: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_local_test: Optional[bool] = None
    is_prod_test: Optional[bool] = None

    class Config:
        orm_mode = True