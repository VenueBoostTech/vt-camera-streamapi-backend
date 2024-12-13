from sqlalchemy.orm import Session
from typing import List
from models.parkingEvent import ParkingEvent
from schemas.parkingEvent import ParkingEventType, ParkingEvent

class CRUDParkingEvent:
    def get_parking_status_by_property(self, db: Session, property_id: str) -> List[ParkingEvent]:
        """
        Retrieve parking status (e.g., occupied spots) for a property.
        """
        return (
            db.query(ParkingEvent)
            .filter(ParkingEvent.property_id == property_id, ParkingEvent.type == ParkingEventType.ENTRY)
            .all()
        )

    def get_parking_analytics_by_zone(self, db: Session, zone_id: str) -> List[ParkingEvent]:
        """
        Retrieve parking analytics for a specific zone.
        """
        return (
            db.query(ParkingEvent)
            .filter(ParkingEvent.zone_id == zone_id)
            .all()
        )

    def get_parking_violations_by_property(self, db: Session, property_id: str) -> List[ParkingEvent]:
        """
        Retrieve parking violations for a specific property.
        """
        return (
            db.query(ParkingEvent)
            .filter(ParkingEvent.property_id == property_id, ParkingEvent.type == ParkingEventType.VIOLATION)
            .all()
        )


parking_event = CRUDParkingEvent()
