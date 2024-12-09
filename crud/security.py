from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.security import ThreatDetection, SleepingDetection
from app.schemas.security import ThreatDetectionCreate, ThreatDetectionUpdate, SleepingDetectionCreate, SleepingDetectionUpdate

class CRUDThreatDetection(CRUDBase[ThreatDetection, ThreatDetectionCreate, ThreatDetectionUpdate]):
    def get_by_severity(self, db: Session, severity: str):
        return db.query(self.model).filter(self.model.severity == severity).all()

class CRUDSleepingDetection(CRUDBase[SleepingDetection, SleepingDetectionCreate, SleepingDetectionUpdate]):
    def get_by_staff(self, db: Session, staff_id: int):
        return db.query(self.model).filter(self.model.staff_id == staff_id).all()

threat_detection = CRUDThreatDetection(ThreatDetection)
sleeping_detection = CRUDSleepingDetection(SleepingDetection)