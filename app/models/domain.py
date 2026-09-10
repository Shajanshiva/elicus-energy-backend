from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    route = relationship("Route", back_populates="users")
    vehicle = relationship("Vehicle", back_populates="users")

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g. "Route A"
    start_location = Column(String(100), nullable=False)
    end_location = Column(String(100), nullable=False)
    route_coordinates = Column(Text, nullable=True)  # JSON string of [{lat, lng, name}]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="route")
    vehicles = relationship("Vehicle", back_populates="route")

    @property
    def waypoints(self):
        if self.route_coordinates:
            try:
                return json.loads(self.route_coordinates)
            except Exception:
                return []
        return []

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. "BUS-001"
    status = Column(String(30), default="active")  # active, idle, offline
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    route = relationship("Route", back_populates="vehicles")
    users = relationship("User", back_populates="vehicle")
    gps_records = relationship("GpsTracking", back_populates="vehicle")
    latest_gps = relationship("LatestGpsLocation", back_populates="vehicle", uselist=False)

class LatestGpsLocation(Base):
    __tablename__ = "latest_gps_locations"

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vehicle = relationship("Vehicle", back_populates="latest_gps")

class GpsTracking(Base):
    __tablename__ = "gps_tracking"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vehicle = relationship("Vehicle", back_populates="gps_records")
