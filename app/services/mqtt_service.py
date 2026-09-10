import json
import logging
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.domain import Vehicle, LatestGpsLocation, GpsTracking

logger = logging.getLogger("mqtt_service")

class MqttSubscriber:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.is_connected = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"Connected successfully to MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            self.is_connected = True
            client.subscribe(settings.MQTT_TOPIC)
            logger.info(f"Subscribed to MQTT topic: {settings.MQTT_TOPIC}")
        else:
            logger.warning(f"Failed to connect to MQTT Broker, return code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            vehicle_code = payload.get("vehicle_id") or payload.get("vehicle_number")
            lat = payload.get("latitude")
            lng = payload.get("longitude")
            speed = payload.get("speed", 0.0)
            
            if not vehicle_code or lat is None or lng is None:
                return

            db = SessionLocal()
            try:
                vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == str(vehicle_code).upper()).first()
                if not vehicle:
                    return

                now = datetime.now(timezone.utc)

                # Upsert latest location
                latest = db.query(LatestGpsLocation).filter(LatestGpsLocation.vehicle_id == vehicle.id).first()
                if not latest:
                    latest = LatestGpsLocation(
                        vehicle_id=vehicle.id,
                        latitude=float(lat),
                        longitude=float(lng),
                        speed=float(speed),
                        timestamp=now
                    )
                    db.add(latest)
                else:
                    latest.latitude = float(lat)
                    latest.longitude = float(lng)
                    latest.speed = float(speed)
                    latest.timestamp = now

                # Add historical log entry
                history_log = GpsTracking(
                    vehicle_id=vehicle.id,
                    latitude=float(lat),
                    longitude=float(lng),
                    speed=float(speed),
                    timestamp=now
                )
                db.add(history_log)
                db.commit()
                logger.info(f"MQTT GPS Updated for {vehicle_code}: {lat}, {lng} @ {speed} km/h")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def start(self):
        try:
            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.warning(f"MQTT Broker connection unavailable ({e}). MQTT ingestion disabled.")

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

mqtt_subscriber = MqttSubscriber()
