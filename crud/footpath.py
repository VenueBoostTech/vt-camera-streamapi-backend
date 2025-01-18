from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from models.footpath import FootpathAnalytics, FootpathPattern
from models.zone import Zone
from models.property import Property
import numpy as np

class CRUDFootpath:
    def create_analytics(
        self,
        db: Session,
        zone_id: str,
        analytics_data: dict,
        business_id: str
    ) -> FootpathAnalytics:
        """Create new footpath analytics entry"""
        # Verify zone belongs to business
        zone = db.query(Zone).filter(
            Zone.id == zone_id,
            Zone.business_id == business_id
        ).first()
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        db_analytics = FootpathAnalytics(
            zone_id=zone_id,
            business_id=business_id,
            property_id=zone.property_id,
            **analytics_data
        )

        db.add(db_analytics)
        db.commit()
        db.refresh(db_analytics)
        return db_analytics

    def get_zone_analytics(
        self,
        db: Session,
        zone_id: str,
        business_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[FootpathAnalytics]:
        """Get analytics for a specific zone"""
        query = db.query(FootpathAnalytics).filter(
            FootpathAnalytics.zone_id == zone_id,
            FootpathAnalytics.business_id == business_id
        )

        if start_time:
            query = query.filter(FootpathAnalytics.timestamp >= start_time)
        if end_time:
            query = query.filter(FootpathAnalytics.timestamp <= end_time)

        return query.order_by(FootpathAnalytics.timestamp.desc()).all()

    def create_pattern(
        self,
        db: Session,
        zone_id: str,
        pattern_data: dict,
        business_id: str
    ) -> FootpathPattern:
        """Create new footpath pattern entry"""
        zone = db.query(Zone).filter(
            Zone.id == zone_id,
            Zone.business_id == business_id
        ).first()
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")

        db_pattern = FootpathPattern(
            zone_id=zone_id,
            business_id=business_id,
            property_id=zone.property_id,
            **pattern_data
        )

        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        return db_pattern

    def get_patterns(
        self,
        db: Session,
        zone_id: str,
        business_id: str,
        min_frequency: int = 2
    ) -> List[FootpathPattern]:
        """Get patterns for a specific zone"""
        return db.query(FootpathPattern).filter(
            FootpathPattern.zone_id == zone_id,
            FootpathPattern.business_id == business_id,
            FootpathPattern.frequency >= min_frequency
        ).order_by(FootpathPattern.frequency.desc()).all()

footpath_crud = CRUDFootpath()