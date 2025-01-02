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

    class Config:
        orm_mode = True
