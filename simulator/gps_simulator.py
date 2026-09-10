import time
import json
import math
import random
import requests
import paho.mqtt.client as mqtt

# MQTT Broker Configuration
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
REST_FALLBACK_URL = "http://127.0.0.1:8000/gps/ingest"

# Vehicle Waypoint Tracks
ROUTE_BUS_001 = [
    (13.0827, 80.2707),  # Central Railway Station
    (13.0780, 80.2650),
    (13.0732, 80.2609),  # Egmore Hub
    (13.0680, 80.2520),
    (13.0626, 80.2430),  # Nungambakkam
    (13.0650, 80.2200),
    (13.0694, 80.1948),  # Koyambedu
    (13.0800, 80.2000),
    (13.0890, 80.2100)   # North Tech Park
]

ROUTE_BUS_002 = [
    (12.9941, 80.1709),  # Airport Terminal
    (13.0000, 80.1880),
    (13.0067, 80.2020),  # Guindy Junction
    (13.0140, 80.2130),
    (13.0213, 80.2231),  # Saidapet Metro
    (13.0320, 80.2290),
    (13.0418, 80.2341),  # T. Nagar
    (13.0460, 80.2420),
    (13.0500, 80.2500)   # South Business Corridor
]

def interpolate_segment(p1, p2, steps=10):
    """Generate smooth intermediate coordinates between two waypoints."""
    points = []
    for i in range(steps):
        t = i / steps
        lat = p1[0] + (p2[0] - p1[0]) * t
        lng = p1[1] + (p2[1] - p1[1]) * t
        points.append((lat, lng))
    return points

def generate_track(waypoints):
    full_track = []
    for i in range(len(waypoints) - 1):
        full_track.extend(interpolate_segment(waypoints[i], waypoints[i+1], steps=8))
    # Return loop
    for i in range(len(waypoints) - 1, 0, -1):
        full_track.extend(interpolate_segment(waypoints[i], waypoints[i-1], steps=8))
    return full_track

def publish_gps(client, vehicle_id, lat, lng, speed):
    payload = {
        "vehicle_id": vehicle_id,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "speed": round(speed, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    topic = f"vehicles/{vehicle_id}/gps"
    published = False
    
    if client and client.is_connected():
        try:
            client.publish(topic, json.dumps(payload))
            print(f"[MQTT] {vehicle_id} -> Topic '{topic}': Lat {payload['latitude']}, Lng {payload['longitude']}, Speed {payload['speed']} km/h")
            published = True
        except Exception as e:
            print(f"[MQTT Error] {e}")

    if not published:
        try:
            res = requests.post(REST_FALLBACK_URL, json=payload, timeout=2)
            if res.status_code == 200:
                print(f"[REST Fallback] {vehicle_id} Ingested: Lat {payload['latitude']}, Lng {payload['longitude']}, Speed {payload['speed']} km/h")
            else:
                print(f"[REST Error] Status {res.status_code}")
        except Exception as e:
            print(f"[Telemetry Ingest Offline] Ensure FastAPI backend is running. ({e})")

def main():
    print("=" * 60)
    print("       GPS VEHICLE TELEMETRY SIMULATOR")
    print("=" * 60)
    print(f"Target MQTT Broker: {MQTT_HOST}:{MQTT_PORT}")
    print(f"Fallback REST URL:  {REST_FALLBACK_URL}")
    print("Simulating BUS-001 (Route A) and BUS-002 (Route B)...\n")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        print("Connected to Mosquitto MQTT Broker.")
    except Exception:
        print("Could not connect to MQTT Broker. Using REST HTTP fallback ingestion.")

    track_1 = generate_track(ROUTE_BUS_001)
    track_2 = generate_track(ROUTE_BUS_002)

    idx1, idx2 = 0, 0

    try:
        while True:
            # BUS-001
            p1 = track_1[idx1]
            speed1 = random.uniform(35.0, 52.0)
            publish_gps(client, "BUS-001", p1[0], p1[1], speed1)

            # BUS-002
            p2 = track_2[idx2]
            speed2 = random.uniform(30.0, 48.0)
            publish_gps(client, "BUS-002", p2[0], p2[1], speed2)

            idx1 = (idx1 + 1) % len(track_1)
            idx2 = (idx2 + 1) % len(track_2)

            time.sleep(3)
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
        if client:
            client.loop_stop()
            client.disconnect()

if __name__ == "__main__":
    main()
