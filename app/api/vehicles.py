from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import User, Vehicle, LatestGpsLocation
from app.schemas.dto import VehicleLocationResponse
from app.api.auth import get_current_user

router = APIRouter(tags=["Vehicle Management & Authorization Enforcement"])

@router.get("/vehicles/{vehicle_number}/location", response_model=VehicleLocationResponse)
def get_vehicle_location_by_number(
    vehicle_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch location for a specific vehicle.
    STRICT BACKEND AUTHORIZATION ENFORCEMENT:
    Users are ONLY permitted to view the location of their assigned vehicle.
    Attempting to view another user's assigned vehicle will return 403 Forbidden.
    """
    assigned_vehicle = None
    if current_user.vehicle_id:
        assigned_vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.vehicle_id).first()

    # Check if requested vehicle_number matches current user's assigned vehicle
    if not assigned_vehicle or assigned_vehicle.vehicle_number.upper() != vehicle_number.upper():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: You are not authorized to view location for vehicle '{vehicle_number}'. Your assigned vehicle is '{assigned_vehicle.vehicle_number if assigned_vehicle else 'None'}'."
        )

    latest_gps = db.query(LatestGpsLocation).filter(LatestGpsLocation.vehicle_id == assigned_vehicle.id).first()
    if not latest_gps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No GPS location telemetry recorded for vehicle '{vehicle_number}'."
        )

    return VehicleLocationResponse(
        vehicle_id=assigned_vehicle.id,
        vehicle_number=assigned_vehicle.vehicle_number,
        latitude=latest_gps.latitude,
        longitude=latest_gps.longitude,
        speed=latest_gps.speed,
        timestamp=latest_gps.timestamp
    )
