from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from schemas.spaceAnalytics import SpaceAnalytics
from schemas.heatmapData import HeatmapData
from schemas.demographics import Demographics
from crud.spaceAnalytics import space_analytics_crud, heatmap_data_crud, demographics_crud
from database import get_db

router = APIRouter()

# GET /api/v1/properties/{id}/analytics
@router.get("/properties/{id}/analytics", response_model=List[SpaceAnalytics])
def get_property_analytics(id: UUID, db: Session = Depends(get_db)):
    analytics = space_analytics_crud.get_by_property(db, property_id=id)
    if not analytics:
        raise HTTPException(status_code=404, detail="No analytics found for this property")
    return analytics


# GET /api/v1/zones/{id}/analytics
@router.get("/zones/{id}/analytics", response_model=List[SpaceAnalytics])
def get_zone_analytics(id: UUID, db: Session = Depends(get_db)):
    analytics = space_analytics_crud.get_by_zone(db, zone_id=id)
    if not analytics:
        raise HTTPException(status_code=404, detail="No analytics found for this zone")
    return analytics


# GET /api/v1/properties/{id}/analytics/heatmaps
@router.get("/properties/{id}/analytics/heatmaps", response_model=List[HeatmapData])
def get_property_heatmaps(id: UUID, db: Session = Depends(get_db)):
    heatmaps = heatmap_data_crud.get_by_property(db, property_id=id)
    if not heatmaps:
        raise HTTPException(status_code=404, detail="No heatmaps found for this property")
    return heatmaps


# GET /api/v1/properties/{id}/analytics/demographics
@router.get("/properties/{id}/analytics/demographics", response_model=List[Demographics])
def get_property_demographics(id: UUID, db: Session = Depends(get_db)):
    demographics = demographics_crud.get_by_property(db, property_id=id)
    if not demographics:
        raise HTTPException(status_code=404, detail="No demographics data found for this property")
    return demographics
