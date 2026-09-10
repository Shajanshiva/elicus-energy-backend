import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vehicle Tracking Backend"
    API_V1_STR: str = ""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_jwt_key_vehicle_tracking_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database: SQLite by default for zero-setup local dev, PostgreSQL for docker
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gps_tracking.db")

    # MQTT Settings
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC: str = "vehicles/+/gps"
    MQTT_ENABLED: bool = True

    class Config:
        case_sensitive = True

settings = Settings()
