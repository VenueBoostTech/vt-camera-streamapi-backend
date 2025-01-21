from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from uuid import UUID
from schemas.spaceAnalytics import SpaceAnalytics
from schemas.heatmapData import HeatmapDataCreate, HeatmapDataResponse, HeatmapPointResponse
from schemas.demographics import DemographicsCreate
from crud.spaceAnalytics import space_analytics_crud, heatmap_data_crud, demographics_crud
from database import get_db
from datetime import datetime, timedelta
import uuid as uid
from models.heatmapData import HeatmapData
from models.zone import Zone
from models.business import Business
from models.property import Property
from models.demographics import Demographics as DemographicsModel
from schemas.demographics import DemographicsCreate as DemographicsSchema, DemographicsResponse
import json
import logging

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
@router.get("/zones/{zone_id}/analytics/heatmaps", response_model=HeatmapDataResponse)
def get_zone_heatmaps(zone_id: UUID, db: Session = Depends(get_db)):
    heatmaps = heatmap_data_crud.get_by_zone(db, zone_id=str(zone_id))  # Explicitly convert UUID to str
    if not heatmaps:
        raise HTTPException(status_code=404, detail="No heatmaps found for this zone")

    points = [
        HeatmapPointResponse(
            camera_id=point.camera_id,
            timestamp=point.timestamp.isoformat(),  # Ensure timestamp is serialized correctly
            x=point.x,
            y=point.y,
            weight=point.weight,
            zone_id=point.zone_id,
        )
        for point in heatmaps
    ]

    return HeatmapDataResponse(points=points)

@router.post("/zones/{zone_id}/analytics/heatmaps", response_model=List[HeatmapDataResponse])
def create_zone_heatmap(zone_id: UUID, heatmap_data: HeatmapDataCreate, db: Session = Depends(get_db)):
    def custom_json_encoder(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
    # Validate zone IDs
    for point in heatmap_data.points:
        if point.zone_id != str(zone_id):
            raise HTTPException(
                status_code=400, 
                detail=f"Zone ID in payload ({point.zone_id}) does not match route ID ({zone_id})"
            )

    # Create heatmap data
    new_heatmaps = heatmap_data_crud.create(db, heatmap_data=heatmap_data)

    # Ensure returned data matches response_model
    response = [
        HeatmapDataResponse(
            points=[
                {
                    "camera_id": point.camera_id,
                    "timestamp": point.timestamp.isoformat(),
                    "x": point.x,
                    "y": point.y,
                    "weight": point.weight,
                    "zone_id": point.zone_id,
                }
            ]
        )
        for point in new_heatmaps
    ]
    return response




# GET /api/v1/properties/{id}/analytics/demographics
@router.get("/zones/{zone_id}/analytics/demographics", response_model=DemographicsResponse)
def get_zone_demographics(
    zone_id: str,
    filter_by: str = Query(..., description="Filter by: day, week, month, quarter"),
    db: Session = Depends(get_db)
):
    now = datetime.now()

    # Calculate the date range based on the filter
    if filter_by == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "quarter":
        quarter = (now.month - 1) // 3 + 1
        start_month = 3 * (quarter - 1) + 1
        start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(status_code=400, detail="Invalid filter. Use 'day', 'week', 'month', or 'quarter'.")

    # Query and aggregate data
    demographics = demographics_crud.get_by_zone_and_date_range(db, zone_id=zone_id, start_date=start_date, end_date=now)
    if not demographics:
        raise HTTPException(status_code=404, detail="No demographics data found for this zone in the selected period")

    # Initialize aggregations
    total_count = 0
    age_groups_data = {}
    gender_distribution = {"Male": 0, "Female": 0}

    # Aggregate data
    for d in demographics:
        for age_group in d.age_groups:
            if age_group["age"] not in age_groups_data:
                age_groups_data[age_group["age"]] = {"count": 0, "male": 0, "female": 0}

            age_groups_data[age_group["age"]]["count"] += age_group["count"]
            age_groups_data[age_group["age"]]["male"] += age_group["male"]
            age_groups_data[age_group["age"]]["female"] += age_group["female"]

        gender_distribution["Male"] += d.gender_distribution.get("Male", 0)
        gender_distribution["Female"] += d.gender_distribution.get("Female", 0)

    total_count = sum(data["count"] for data in age_groups_data.values())

    age_groups_list = [
        {"age": age, "count": data["count"], "male": data["male"], "female": data["female"]}
        for age, data in age_groups_data.items()
    ]

    return Demographics(
        id=uid.uuid4(),
        zone_id=zone_id,
        timestamp=now,
        total_count=total_count,
        age_groups=age_groups_list,
        gender_distribution=gender_distribution
    )

@router.get("/analytics/demographics", response_model=DemographicsSchema)
def get_zone_demographics(
    zone_id: Optional[str] = Query(None, description="Zone ID to filter by"),
    filter_by: str = Query(..., description="Filter by: day, week, month, quarter"),
    db: Session = Depends(get_db),
    business_id: Optional[str] = Header(None, alias="X-VT-Business-ID")
):
    now = datetime.now()

    # Calculate the date range based on the filter
    if filter_by == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "quarter":
        quarter = (now.month - 1) // 3 + 1
        start_month = 3 * (quarter - 1) + 1
        start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(status_code=400, detail="Invalid filter. Use 'day', 'week', 'month', or 'quarter'.")

    # If both zone_id and business_id are provided, prioritize zone_id
    if zone_id:
        zone_ids = [zone_id]
    elif business_id:
        business = db.query(Business).filter(Business.id == business_id, Business.is_active == True).first()
        if not business:
            raise HTTPException(status_code=401, detail="Invalid or unauthorized business")

        properties = db.query(Property).filter(Property.business_id == business_id).all()
        if not properties:
            raise HTTPException(status_code=404, detail="No properties found for the provided business ID")

        property_ids = [property.id for property in properties]
        zones = db.query(Zone).filter(Zone.property_id.in_(property_ids)).all()
        zone_ids = [zone.id for zone in zones]
    else:
        raise HTTPException(status_code=400, detail="Either zone_id or business_id must be provided")

    # Fetch demographics for all zones in a single query
    demographics = db.query(DemographicsModel).filter(
        DemographicsModel.zone_id.in_(zone_ids),
        DemographicsModel.timestamp >= start_date,
        DemographicsModel.timestamp <= now
    ).all()

    if not demographics:
        raise HTTPException(status_code=404, detail="No demographics data found for the selected criteria")

    # Initialize aggregation containers
    aggregated_data = {
        "total_count": 0,
        "age_groups_data": {},
        "gender_distribution": {"Male": 0, "Female": 0}
    }

    for d in demographics:
        # Aggregate age groups
        for age_group in d.age_groups:
            if age_group["age"] not in aggregated_data["age_groups_data"]:
                aggregated_data["age_groups_data"][age_group["age"]] = {"count": 0, "male": 0, "female": 0}

            aggregated_data["age_groups_data"][age_group["age"]]["count"] += age_group["count"]
            aggregated_data["age_groups_data"][age_group["age"]]["male"] += age_group["male"]
            aggregated_data["age_groups_data"][age_group["age"]]["female"] += age_group["female"]

        # Aggregate gender distribution
        aggregated_data["gender_distribution"]["Male"] += d.gender_distribution.get("Male", 0)
        aggregated_data["gender_distribution"]["Female"] += d.gender_distribution.get("Female", 0)

        # Increment total count
        aggregated_data["total_count"] += sum(age_group["count"] for age_group in d.age_groups)

    # Prepare single combined response
    age_groups_list = [
        {"age": age, "count": group_data["count"], "male": group_data["male"], "female": group_data["female"]}
        for age, group_data in aggregated_data["age_groups_data"].items()
    ]

    response = DemographicsSchema(
        id=uid.uuid4(),
        zone_id="aggregated",  # Use a placeholder for aggregated data
        timestamp=now,
        total_count=aggregated_data["total_count"],
        age_groups=age_groups_list,
        gender_distribution=aggregated_data["gender_distribution"]
    )

    return response


@router.get("/properties/{property_id}/analytics/demographics", response_model=Dict)
def get_property_demographics(
    property_id: str,
    filter_by: str = Query(..., description="Filter by: day, week, month, quarter"),
    db: Session = Depends(get_db)
):
    now = datetime.now()

    # Calculate the date range based on the filter
    if filter_by == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif filter_by == "quarter":
        quarter = (now.month - 1) // 3 + 1
        start_month = 3 * (quarter - 1) + 1
        start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(status_code=400, detail="Invalid filter. Use 'day', 'week', 'month', or 'quarter'.")

    # Query and aggregate data
    demographics = demographics_crud.get_by_property_id_and_date_range(
        db, property_id=property_id, start_date=start_date, end_date=now
    )
    if not demographics:
        raise HTTPException(status_code=404, detail="No demographics data found for this property in the selected period")

    # Initialize aggregations
    total_count = 0
    age_groups_data = {}
    gender_distribution = {"Male": 0, "Female": 0}

    # Aggregate data across all zones
    for d in demographics:
        for age_group in d.age_groups:
            if age_group["age"] not in age_groups_data:
                age_groups_data[age_group["age"]] = {"count": 0, "male": 0, "female": 0}

            age_groups_data[age_group["age"]]["count"] += age_group["count"]
            age_groups_data[age_group["age"]]["male"] += age_group["male"]
            age_groups_data[age_group["age"]]["female"] += age_group["female"]

        gender_distribution["Male"] += d.gender_distribution.get("Male", 0)
        gender_distribution["Female"] += d.gender_distribution.get("Female", 0)

    total_count = sum(data["count"] for data in age_groups_data.values())

    age_groups_list = [
        {"age": age, "count": data["count"], "male": data["male"], "female": data["female"]}
        for age, data in age_groups_data.items()
    ]

    return {
        "property_id": property_id,
        "timestamp": now,
        "total_count": total_count,
        "age_groups": age_groups_list,
        "gender_distribution": gender_distribution
    }

@router.get("/analytics/heatmaps", response_model=HeatmapDataResponse)
def get_heatmap_data(
    zone_id: Optional[str] = Query(None, description="Zone ID to filter by"),
    filter_by: str = Query(..., description="Filter by: last_24_hours, last_week, last_month"),
    db: Session = Depends(get_db),
    business_id: Optional[str] = Header(None, alias="X-VT-Business-ID")
):
    logger.debug(f"Received request with zone_id={zone_id}, filter_by={filter_by}, business_id={business_id}")

    now = datetime.now()
    
    # Calculate the date range based on the filter
    if filter_by == "last_24_hours":
        start_date = now - timedelta(hours=24)
    elif filter_by == "last_week":
        start_date = now - timedelta(weeks=1)
    elif filter_by == "last_month":
        start_date = now - timedelta(days=30)
    else:
        logger.error("Invalid filter value received")
        raise HTTPException(status_code=400, detail="Invalid filter. Use 'last_24_hours', 'last_week', or 'last_month'.")

    logger.debug(f"Date range calculated: start_date={start_date}, end_date={now}")

    # Determine the zone IDs to query
    if zone_id:
        zone_ids = [zone_id]
    elif business_id:
        logger.debug("Fetching zones for business_id")
        business = db.query(Business).filter(Business.id == business_id, Business.is_active == True).first()
        if not business:
            logger.error("Invalid or unauthorized business")
            raise HTTPException(status_code=401, detail="Invalid or unauthorized business")

        properties = db.query(Property).filter(Property.business_id == business_id).all()
        if not properties:
            logger.error("No properties found for the provided business ID")
            raise HTTPException(status_code=404, detail="No properties found for the provided business ID")

        property_ids = [property.id for property in properties]
        zones = db.query(Zone).filter(Zone.property_id.in_(property_ids)).all()
        zone_ids = [zone.id for zone in zones]
    else:
        logger.error("Neither zone_id nor business_id was provided")
        raise HTTPException(status_code=400, detail="Either zone_id or business_id must be provided")

    logger.debug(f"Zone IDs to query: {zone_ids}")

    # Query heatmap data
    logger.debug("Querying heatmap data from the database")
    heatmap_points = db.query(HeatmapData).filter(
        HeatmapData.zone_id.in_(zone_ids),
        HeatmapData.timestamp >= start_date,
        HeatmapData.timestamp <= now
    ).all()

    logger.debug(f"Heatmap points retrieved: {heatmap_points}")

    if not heatmap_points:
        logger.error("No heatmap data found for the selected criteria")
        raise HTTPException(status_code=404, detail="No heatmap data found for the selected criteria")

    # Aggregate the heatmap points
    aggregated_points = [
        {
            "camera_id": point.camera_id,
            "timestamp": point.timestamp.isoformat(),
            "x": point.x,
            "y": point.y,
            "weight": point.weight,
            "zone_id": point.zone_id,
        }
        for point in heatmap_points
    ]

    response = HeatmapDataResponse(
        id=uid.uuid4(),
        points=aggregated_points,
    )

    logger.debug(f"Response prepared: {response}")

    return response

@router.post("/zones/{zone_id}/analytics/demographics", response_model=DemographicsResponse)
def create_zone_demographics(
    zone_id: str,
    demographics_data: DemographicsCreate,
    db: Session = Depends(get_db)
):
    if demographics_data.zone_id != zone_id:
        raise HTTPException(status_code=400, detail="Zone ID in payload does not match route ID")

    new_demographics = demographics_crud.create(db, demographics_data=demographics_data)
    return new_demographics