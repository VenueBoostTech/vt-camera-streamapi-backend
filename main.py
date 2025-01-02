from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import camera,entry_exit,analytics,vehicle_detection,smoking_detection,threat_detection,environment,security,staff,vehicle,activity,dashboard,property,zone,behavior,pattern, spaceAnalytics, securityEvent, incident, parkingEvent, parkingAnalytics, business, business_super_admin

app = FastAPI(
    title="VisionTrackAPI",
    redirect_slashes=True
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(camera.router, prefix="/api/camera", tags=["camera"])
app.include_router(entry_exit.router, prefix="/api", tags=["entry_exit"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(vehicle_detection.router, prefix="/api/vehicle", tags=["vehicle"])
app.include_router(smoking_detection.router, prefix="/api/smoking", tags=["smoking"])
app.include_router(threat_detection.router, prefix="/api/threat", tags=["threat"])
app.include_router(activity.router, prefix="/optivenue/api/v1/activity", tags=["Activity"])
app.include_router(dashboard.router, prefix="/optivenue/api/v1/dashboard", tags=["Dashboard"])
app.include_router(environment.router, prefix="/optivenue/api/v1/environment", tags=["Environment"])
app.include_router(security.router, prefix="/vt/api/v1/security", tags=["Security"])
app.include_router(property.router, prefix="/vt/api/v1/property", tags=["Property"])
app.include_router(zone.router, prefix="/vt/api/v1/zone", tags=["Zone"])
app.include_router(behavior.router, prefix="/vt/api/v1/behavior", tags=["Behavior"])
app.include_router(pattern.router, prefix="/vt/api/v1/pattern", tags=["Pattern"])
app.include_router(spaceAnalytics.router, prefix="/vt/api/v1/spaceAnalytics", tags=["Space Analytics"])
app.include_router(securityEvent.router, prefix="/vt/api/v1/securityEvent", tags=["Security Events"])
app.include_router(incident.router, prefix="/vt/api/v1/incident", tags=["Incidents"])
app.include_router(parkingEvent.router, prefix="/vt/api/v1/parkingEvent", tags=["Parking Events"])
app.include_router(parkingAnalytics.router, prefix="/vt/api/v1/parkingAnalytics", tags=["Parking Analytics"])
# app.include_router(settings_router, prefix="/settings", tags=["Settings"])
app.include_router(staff.router, prefix="/optivenue/api/v1/staff", tags=["Staff"])
app.include_router(vehicle.router, prefix="/optivenue/api/v1/vehicle", tags=["Vehicle"])
app.include_router(business.router, prefix="/api/businesses", tags=["Businesses"])
app.include_router(business_super_admin.router, prefix="/api/superadmin/businesses", tags=["Super Admin"])


@app.get("/")
def read_root():
    return {"message": "VisionTrack API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)