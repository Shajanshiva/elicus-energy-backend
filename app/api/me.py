from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import User, Route, Vehicle, LatestGpsLocation, GpsTracking
from app.schemas.dto import (
    MeAssignmentResponse, UserDto, RouteDto, VehicleDto,
    VehicleLocationResponse, GpsHistoryItem
)
from app.api.auth import get_current_user

router = APIRouter(tags=["User Assignments & Vehicle Telemetry"])

@router.get("/me/assignment", response_model=MeAssignmentResponse)
def get_my_assignment(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch currently logged in user's assigned route and assigned vehicle."""
    user_dto = UserDto.model_validate(current_user)

    route_dto = None
    if current_user.route_id:
        route = db.query(Route).filter(Route.id == current_user.route_id).first()
        if route:
            route_dto = RouteDto(
                id=route.id,
                name=route.name,
                start_location=route.start_location,
                end_location=route.end_location,
                waypoints=route.waypoints
            )

    vehicle_dto = None
    if current_user.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.vehicle_id).first()
        if vehicle:
            vehicle_dto = VehicleDto.model_validate(vehicle)

    return MeAssignmentResponse(user=user_dto, route=route_dto, vehicle=vehicle_dto)

@router.get("/me/vehicle/location", response_model=VehicleLocationResponse)
def get_my_vehicle_location(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch latest real-time GPS location of the current user's assigned vehicle."""
    if not current_user.vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to current user."
        )

    vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Assigned vehicle not found.")

    latest_gps = db.query(LatestGpsLocation).filter(LatestGpsLocation.vehicle_id == vehicle.id).first()
    if not latest_gps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No GPS signal received yet for vehicle '{vehicle.vehicle_number}'."
        )

    return VehicleLocationResponse(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        latitude=latest_gps.latitude,
        longitude=latest_gps.longitude,
        speed=latest_gps.speed,
        timestamp=latest_gps.timestamp
    )

@router.get("/me/vehicle/history", response_model=List[GpsHistoryItem])
def get_my_vehicle_history(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch historical GPS trajectory log for current user's assigned vehicle."""
    if not current_user.vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to current user."
        )

    logs = (
        db.query(GpsTracking)
        .filter(GpsTracking.vehicle_id == current_user.vehicle_id)
        .order_by(GpsTracking.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        GpsHistoryItem(
            latitude=log.latitude,
            longitude=log.longitude,
            speed=log.speed,
            timestamp=log.timestamp
        )
        for log in logs
    ]
