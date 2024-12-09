# # app/api/settings.py

# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from typing import Optional
# from datetime import datetime
# from core.database import get_db
# import crud, schemas

# router = APIRouter()

# @router.get("/monitoring-parameters", response_model=schemas.MonitoringParameters)
# async def get_monitoring_parameters(
#     db: Session = Depends(get_db),
#     dummy: bool = Query(False, description="Use dummy data for testing")
# ):
#     """
#     Retrieve the current monitoring parameters.

#     - **dummy**: If set to True, returns dummy data for testing purposes
#     """
#     if dummy:
#         # Fallback use case data for testing purposes
#         return schemas.MonitoringParameters(
#             max_break_duration=30,
#             min_activity_level="medium",
#             max_sleeping_duration=10
#         )
    
#     parameters = crud.settings.get_monitoring_parameters(db)
#     if not parameters:
#         raise HTTPException(status_code=404, detail="Monitoring parameters not found")
#     return parameters

# @router.put("/monitoring-parameters", response_model=schemas.MonitoringParameters)
# async def update_monitoring_parameters(
#     data: schemas.MonitoringParametersUpdate,
#     db: Session = Depends(get_db),
#     dummy: bool = Query(False, description="Use dummy data for testing")
# ):
#     """
#     Update the monitoring parameters.

#     - **data**: The new parameter values to be updated
#     - **dummy**: If set to True, returns dummy data for testing purposes
#     """
#     if dummy:
#         # Fallback use case data for testing purposes
#         return schemas.MonitoringParameters(
#             max_break_duration=data.max_break_duration or 30,
#             min_activity_level=data.min_activity_level or "medium",
#             max_sleeping_duration=data.max_sleeping_duration or 10
#         )

#     if not data:
#         raise HTTPException(status_code=400, detail="Data is required")
    
#     try:
#         updated_parameters = crud.settings.update_monitoring_parameters(db, data)
#         if not updated_parameters:
#             raise HTTPException(status_code=404, detail="Monitoring parameters not found")
#         return updated_parameters
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @router.get("/monitoring-summary", response_model=schemas.MonitoringSummary)
# async def get_monitoring_summary(
#     db: Session = Depends(get_db),
#     start_date: Optional[datetime] = Query(None, description="Filter by start date"),
#     end_date: Optional[datetime] = Query(None, description="Filter by end date"),
#     dummy: bool = Query(False, description="Use dummy data for testing")
# ):
#     """
#     Retrieve a summary of monitoring data.

#     - **start_date**: Optional. Filter summary data starting from this date
#     - **end_date**: Optional. Filter summary data up to this date
#     - **dummy**: If set to True, returns dummy data for testing purposes
#     """
#     if dummy:
#         # Fallback use case data for testing purposes
#         return schemas.MonitoringSummary(
#             total_activities=150,
#             total_breaks=30,
#             total_sleeping_instances=5
#         )

#     try:
#         return crud.settings.get_monitoring_summary(db, start_date, end_date)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))