from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.environment import SmokeDetection
from app.schemas.environment import SmokeDetectionCreate, SmokeDetectionUpdate

class CRUDSmokeDetection(CRUDBase[SmokeDetection, SmokeDetectionCreate, SmokeDetectionUpdate]):
    def get_active_alarms(self, db: Session):
        return db.query(self.model).filter(self.model.is_alarm_triggered == True).all()

smoke_detection = CRUDSmokeDetection(SmokeDetection)