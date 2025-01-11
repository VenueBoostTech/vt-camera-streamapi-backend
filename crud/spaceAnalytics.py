from sqlalchemy.orm import Session
from models.spaceAnalytics import SpaceAnalytics
from models.demographics import Demographics
from models.heatmapData import HeatmapData
from schemas.heatmapData import HeatmapDataCreate
from schemas.demographics import DemographicsCreate
from models.zone import Zone
from uuid import UUID
import datetime
from typing import List

class SpaceAnalyticsCRUD:
    def get_by_property(self, db: Session, property_id: UUID):
        return db.query(SpaceAnalytics).filter(SpaceAnalytics.property_id == property_id).all()

    def get_by_zone(self, db: Session, zone_id: UUID):
        return db.query(SpaceAnalytics).filter(SpaceAnalytics.zone_id == zone_id).all()

space_analytics_crud = SpaceAnalyticsCRUD()

class DemographicsCRUD:
    def get_by_zone(self, db: Session, zone_id: str) -> List[Demographics]:
        """Fetch all demographics for a specific zone."""
        return db.query(Demographics).filter(Demographics.zone_id == zone_id).all()

    def create(self, db: Session, demographics_data: DemographicsCreate) -> Demographics:
        """Create a new demographics entry."""
        data = demographics_data.dict(exclude_unset=True)
        new_demographics = Demographics(**data)
        db.add(new_demographics)
        db.commit()
        db.refresh(new_demographics)
        return new_demographics

    def get_by_zone_and_date_range(self, db: Session, zone_id: str, start_date: datetime, end_date: datetime) -> List[Demographics]:
        """Fetch demographics data for a specific zone within a date range."""
        return db.query(Demographics).filter(
            Demographics.zone_id == zone_id,
            Demographics.timestamp >= start_date,
            Demographics.timestamp <= end_date
        ).all()

    def get_by_property_id_and_date_range(self, db: Session, property_id: str, start_date: datetime, end_date: datetime) -> List[Demographics]:
        return db.query(Demographics).join(Zone).filter(
            Zone.property_id == property_id,
            Demographics.timestamp >= start_date,
            Demographics.timestamp <= end_date
        ).all()

# Create an instance of DemographicsCRUD
demographics_crud = DemographicsCRUD()

class HeatmapDataCRUD:
    def get_by_zone(self, db: Session, zone_id: str) -> List[HeatmapData]:
        """Fetch all heatmap points for a specific zone."""
        return db.query(HeatmapData).filter(HeatmapData.zone_id == str(zone_id)).all()

    def create(self, db: Session, heatmap_data: HeatmapDataCreate) -> List[HeatmapData]:
        """Create multiple heatmap points."""
        new_points = [
            HeatmapData(
                camera_id=point.camera_id,
                timestamp=point.timestamp,
                x=point.x,
                y=point.y,
                weight=point.weight,
                zone_id=point.zone_id,
            )
            for point in heatmap_data.points
        ]
        db.add_all(new_points)
        db.commit()
        return new_points


heatmap_data_crud = HeatmapDataCRUD()
