import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.domain import User, Route, Vehicle, LatestGpsLocation, GpsTracking
from app.core.security import get_password_hash

def seed_db(db: Session):
    Base.metadata.create_all(bind=engine)

    # Check if already seeded by looking up user or vehicle
    if db.query(User).filter(User.email == "usera@test.com").first() or db.query(Vehicle).filter(Vehicle.vehicle_number == "BUS-001").first():
        return

    print("Seeding database with test users, routes, and vehicles...")

    # 1. Routes (Using Chennai coordinates matching assessment example: 13.0827, 80.2707)
    waypoints_a = [
        {"name": "Central Railway Station", "latitude": 13.0827, "longitude": 80.2707},
        {"name": "Egmore Hub", "latitude": 13.0732, "longitude": 80.2609},
        {"name": "Nungambakkam High Rd", "latitude": 13.0626, "longitude": 80.2430},
        {"name": "Koyambedu Bus Terminal", "latitude": 13.0694, "longitude": 80.1948},
        {"name": "North Tech Park", "latitude": 13.0890, "longitude": 80.2100}
    ]
    route_a = Route(
        name="Route A",
        start_location="Central Railway Station",
        end_location="North Tech Park",
        route_coordinates=json.dumps(waypoints_a)
    )

    waypoints_b = [
        {"name": "Airport Terminal", "latitude": 12.9941, "longitude": 80.1709},
        {"name": "Guindy Junction", "latitude": 13.0067, "longitude": 80.2020},
        {"name": "Saidapet Metro", "latitude": 13.0213, "longitude": 80.2231},
        {"name": "T. Nagar Shopping Zone", "latitude": 13.0418, "longitude": 80.2341},
        {"name": "South Business Corridor", "latitude": 13.0500, "longitude": 80.2500}
    ]
    route_b = Route(
        name="Route B",
        start_location="Airport Terminal",
        end_location="South Business Corridor",
        route_coordinates=json.dumps(waypoints_b)
    )
    db.add_all([route_a, route_b])
    db.commit()

    # 2. Vehicles
    bus_001 = Vehicle(
        vehicle_number="BUS-001",
        status="active",
        route_id=route_a.id
    )
    bus_002 = Vehicle(
        vehicle_number="BUS-002",
        status="active",
        route_id=route_b.id
    )
    db.add_all([bus_001, bus_002])
    db.commit()

    # 3. Users
    user_a = User(
        email="usera@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="User A",
        route_id=route_a.id,
        vehicle_id=bus_001.id
    )
    user_b = User(
        email="userb@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="User B",
        route_id=route_b.id,
        vehicle_id=bus_002.id
    )
    db.add_all([user_a, user_b])
    db.commit()

    # 4. Initial Telemetry & History
    now = datetime.now(timezone.utc)
    
    loc_1 = LatestGpsLocation(
        vehicle_id=bus_001.id,
        latitude=13.0827,
        longitude=80.2707,
        speed=42.5,
        timestamp=now
    )
    loc_2 = LatestGpsLocation(
        vehicle_id=bus_002.id,
        latitude=12.9941,
        longitude=80.1709,
        speed=38.0,
        timestamp=now
    )
    db.add_all([loc_1, loc_2])

    # Initial history logs for BUS-001
    for wp in waypoints_a[:3]:
        db.add(GpsTracking(
            vehicle_id=bus_001.id,
            latitude=wp["latitude"],
            longitude=wp["longitude"],
            speed=40.0,
            timestamp=now
        ))

    # Initial history logs for BUS-002
    for wp in waypoints_b[:3]:
        db.add(GpsTracking(
            vehicle_id=bus_002.id,
            latitude=wp["latitude"],
            longitude=wp["longitude"],
            speed=36.0,
            timestamp=now
        ))

    db.commit()
    print("Database successfully seeded with User A (BUS-001) & User B (BUS-002)!")

if __name__ == "__main__":
    db = SessionLocal()
    seed_db(db)
    db.close()
