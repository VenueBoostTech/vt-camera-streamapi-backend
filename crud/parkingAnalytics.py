from sqlalchemy.orm import Session
from typing import List, Optional
from models.parkingAnalytics import ParkingAnalytics
from schemas.parkingAnalytics import ParkingAnalytics as ParkingAnalyticsSchema

class CRUDParkingAnalytics:
    def get_vehicle_analytics_by_property(self, db: Session, property_id: str) -> List[ParkingAnalyticsSchema]:
        """
        Retrieve vehicle analytics for a property.
        """
        return db.query(ParkingAnalytics).filter(ParkingAnalytics.property_id == property_id).all()

    def get_vehicle_patterns_by_zone(self, db: Session, zone_id: str) -> Optional[ParkingAnalyticsSchema]:
        """
        Retrieve vehicle patterns for a specific zone.
        """
        return db.query(ParkingAnalytics).filter(ParkingAnalytics.zone_id == zone_id).all()


parking_analytics = CRUDParkingAnalytics()
