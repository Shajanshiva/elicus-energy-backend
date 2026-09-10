from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Vehicle, LatestGpsLocation, GpsTracking
from app.schemas.dto import GpsIngestPayload, VehicleLocationResponse

router = APIRouter(tags=["GPS Telemetry Ingestion"])

@router.post("/gps/ingest", response_model=VehicleLocationResponse)
def ingest_gps_point(payload: GpsIngestPayload, db: Session = Depends(get_db)):
    """
    Ingest real-time GPS coordinate update (REST Ingestion Fallback).
    Updates latest location and saves historical GPS tracking record.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == payload.vehicle_id.upper()).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle '{payload.vehicle_id}' not found."
        )

    ts = payload.timestamp or datetime.now(timezone.utc)

    # 1. Upsert LatestGpsLocation
    latest_gps = db.query(LatestGpsLocation).filter(LatestGpsLocation.vehicle_id == vehicle.id).first()
    if not latest_gps:
        latest_gps = LatestGpsLocation(
            vehicle_id=vehicle.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            speed=payload.speed,
            timestamp=ts
        )
        db.add(latest_gps)
    else:
        latest_gps.latitude = payload.latitude
        latest_gps.longitude = payload.longitude
        latest_gps.speed = payload.speed
        latest_gps.timestamp = ts

    # 2. Append to GpsTracking history
    history_record = GpsTracking(
        vehicle_id=vehicle.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        timestamp=ts
    )
    db.add(history_record)
    db.commit()

    return VehicleLocationResponse(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        latitude=latest_gps.latitude,
        longitude=latest_gps.longitude,
        speed=latest_gps.speed,
        timestamp=latest_gps.timestamp
    )
