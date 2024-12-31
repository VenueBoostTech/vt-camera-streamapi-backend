from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class BusinessSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    vt_platform_id: str
    api_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
