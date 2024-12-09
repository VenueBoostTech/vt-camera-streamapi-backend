from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.staff import Staff, WorkSession, Activity, Break
from app.schemas.staff import StaffCreate, StaffUpdate, WorkSessionCreate, ActivityCreate, BreakCreate

class CRUDStaff(CRUDBase[Staff, StaffCreate, StaffUpdate]):
    def get_work_activity(self, db: Session, staff_id: int):
        return db.query(WorkSession).filter(WorkSession.staff_id == staff_id).all()

    def get_working_sessions(self, db: Session):
        return db.query(WorkSession).all()

    def monitor_breaks(self, db: Session, break_data: BreakCreate):
        db_break = Break(**break_data.dict())
        db.add(db_break)
        db.commit()
        db.refresh(db_break)
        return db_break

staff = CRUDStaff(Staff)