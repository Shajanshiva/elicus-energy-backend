from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str

class RouteDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    start_location: str
    end_location: str
    waypoints: List[Any] = []

class VehicleDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_number: str
    status: str

class MeAssignmentResponse(BaseModel):
    user: UserDto
    route: Optional[RouteDto] = None
    vehicle: Optional[VehicleDto] = None

class VehicleLocationResponse(BaseModel):
    vehicle_id: int
    vehicle_number: str
    latitude: float
    longitude: float
    speed: float
    timestamp: datetime

class GpsHistoryItem(BaseModel):
    latitude: float
    longitude: float
    speed: float
    timestamp: datetime

class GpsIngestPayload(BaseModel):
    vehicle_id: str  # e.g. BUS-001
    latitude: float
    longitude: float
    speed: float = 0.0
    timestamp: Optional[datetime] = None
