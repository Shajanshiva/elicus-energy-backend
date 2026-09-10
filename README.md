# Vehicle Tracking Backend Service (FastAPI + PostgreSQL/SQLite + MQTT)

Production-ready backend service built with **Python FastAPI**, **SQLAlchemy ORM**, **JWT Authentication**, and **Mosquitto MQTT** for real-time GPS vehicle tracking, route assignment, and role-based authorization enforcement.

---

## 🌟 Key Features

* **JWT Authentication**: Secure user login generating Bearer tokens (`/auth/login`).
* **Strict Backend Authorization**: Enforces user route & vehicle isolation. If User A (assigned to `BUS-001`) requests `GET /vehicles/BUS-002/location`, the backend rejects the request with **HTTP 403 Forbidden**.
* **Dual GPS Ingestion**:
  * **MQTT Subscriber**: Subscribes to `vehicles/{vehicle_id}/gps` on Mosquitto broker using `paho-mqtt`.
  * **REST API Fallback**: Ingestion via `POST /gps/ingest`.
* **Telemetry Storage**: Stores both real-time latest locations (`latest_gps_locations`) and historical trail logs (`gps_tracking`).
* **Built-in Web Preview**: Interactive Leaflet.js dashboard packaged inside static files for browser demonstration (`/preview/index.html`).
* **Docker Compose Setup**: One-command initialization for FastAPI, PostgreSQL, Mosquitto MQTT, and GPS Simulator.

---

## 📊 Database Schema Design

```
+-----------------------------------+
|               users               |
+-----------------------------------+
| id (PK)                           |
| email (Unique)                    |
| hashed_password                   |
| full_name                         |
| route_id (FK -> routes.id)        |
| vehicle_id (FK -> vehicles.id)    |
| created_at                        |
+-----------------------------------+
                 |
                 +-----------------------+
                 |                       |
                 v                       v
+---------------------------------+ +-----------------------------------+
|             routes              | |             vehicles              |
+---------------------------------+ +-----------------------------------+
| id (PK)                         | | id (PK)                           |
| name ("Route A")                | | vehicle_number ("BUS-001")        |
| start_location                  | | status ("active")                 |
| end_location                    | | route_id (FK -> routes.id)        |
| route_coordinates (JSON)        | | created_at                        |
| created_at                      | +-----------------------------------+
+---------------------------------+                   |
                                                      v
                                    +-----------------------------------+
                                    |           gps_tracking            |
                                    +-----------------------------------+
                                    | id (PK)                           |
                                    | vehicle_id (FK -> vehicles.id)    |
                                    | latitude                          |
                                    | longitude                         |
                                    | speed                             |
                                    | timestamp                         |
                                    +-----------------------------------+
```

---

## 🚀 Quick Start (Local Run)

### 1. Install Dependencies & Run Server
```bash
# Navigate to backend directory
cd vehicle-tracking-backend

# Install python dependencies
pip install -r requirements.txt

# Start FastAPI server (Auto-seeds database with User A and User B)
uvicorn app.main:app --reload --port 8000
```

* **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Live Interactive Web Preview**: [http://127.0.0.1:8000/preview/index.html](http://127.0.0.1:8000/preview/index.html)

---

## 🚍 Running the Real-Time GPS Simulator

Simulates vehicles (`BUS-001` and `BUS-002`) emitting live GPS coordinates every 3 seconds over MQTT / REST:

```bash
python simulator/gps_simulator.py
```

---

## 🐳 Docker Compose Deployment (Bonus)

```bash
# Spin up FastAPI + PostgreSQL + Mosquitto MQTT + GPS Simulator
docker compose up --build
```

---

## 🔑 Demo Credentials

| Role | Email | Password | Assigned Route | Assigned Vehicle |
| :--- | :--- | :--- | :--- | :--- |
| **User A** | `usera@test.com` | `password123` | Route A | `BUS-001` |
| **User B** | `userb@test.com` | `password123` | Route B | `BUS-002` |

---

## 🛡️ Testing Authorization Enforcement

Run automated unit tests verifying login and 403 Forbidden enforcement:

```bash
python -m pytest tests/test_authorization.py
```

### Manual Security Demonstration:
1. Log in as `User A` (`usera@test.com`) to get JWT Token.
2. Send request: `GET /vehicles/BUS-002/location` with User A's token.
3. Backend returns:
```json
{
  "detail": "Access Denied: You are not authorized to view location for vehicle 'BUS-002'. Your assigned vehicle is 'BUS-001'."
}
```
`(HTTP Status: 403 Forbidden)`
"# elicus-energy-backend" 
