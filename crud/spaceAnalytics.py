from sqlalchemy.orm import Session
from models.spaceAnalytics import SpaceAnalytics
from models.demographics import Demographics
from models.heatmapData import HeatmapData
from uuid import UUID

class SpaceAnalyticsCRUD:
    def get_by_property(self, db: Session, property_id: UUID):
        return db.query(SpaceAnalytics).filter(SpaceAnalytics.property_id == property_id).all()

    def get_by_zone(self, db: Session, zone_id: UUID):
        return db.query(SpaceAnalytics).filter(SpaceAnalytics.zone_id == zone_id).all()

space_analytics_crud = SpaceAnalyticsCRUD()

class DemographicsCRUD:
    def get_by_property(self, db: Session, property_id: UUID):
        return db.query(Demographics).filter(Demographics.property_id == property_id).all()

demographics_crud = DemographicsCRUD()

class HeatmapDataCRUD:
    def get_by_property(self, db: Session, property_id: UUID):
        return db.query(HeatmapData).filter(HeatmapData.property_id == property_id).all()

heatmap_data_crud = HeatmapDataCRUD()