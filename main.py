from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import camera, entry_exit, analytics, vehicle_detection, smoking_detection, threat_detection

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(camera.router, prefix="/api/camera", tags=["camera"])
app.include_router(entry_exit.router, prefix="/api", tags=["entry_exit"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(vehicle_detection.router, prefix="/api/vehicle", tags=["vehicle"])
app.include_router(smoking_detection.router, prefix="/api/smoking", tags=["smoking"])
app.include_router(threat_detection.router, prefix="/api/threat", tags=["threat"])

@app.get("/")
def read_root():
    return {"message": "VisionTrack API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)