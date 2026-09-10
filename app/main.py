import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.db.seed import seed_db
from app.api.auth import router as auth_router
from app.api.me import router as me_router
from app.api.vehicles import router as vehicles_router
from app.api.gps import router as gps_router
from app.services.mqtt_service import mqtt_subscriber

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
    
    if settings.MQTT_ENABLED:
        mqtt_subscriber.start()
        
    yield
    
    # Shutdown actions
    if settings.MQTT_ENABLED:
        mqtt_subscriber.stop()

app = FastAPI(
    title="Vehicle Tracking Backend API",
    description="FastAPI Service for GPS Vehicle Tracking, User Route & Vehicle Authorization, and Telemetry Storage.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Flutter Mobile & Web client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(vehicles_router)
app.include_router(gps_router)

# Mount Web Preview Dashboard Static Files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/preview", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/")
def root():
    return {
        "message": "Vehicle Tracking API Service is active",
        "docs_url": "/docs",
        "web_preview": "/preview/index.html",
        "version": "1.0.0"
    }
