"""
RideRakshak Backend Configuration
All configurable parameters in one place.
"""

import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # App
    APP_NAME: str = "RideRakshak"
    APP_VERSION: str = "1.0.0-mvp"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./riderakshak.db"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Simulation
    SIMULATION_MODE: bool = True
    DEFAULT_RIDER_ID: str = "RR001"

    # GPS defaults (Pune, Maharashtra, India)
    DEFAULT_LATITUDE: float = 18.5204
    DEFAULT_LONGITUDE: float = 73.8567

    # False alert cancellation window in seconds
    CANCELLATION_WINDOW_SECONDS: int = 10

    # ── Accident Detection Thresholds ─────────────────────────────────────────
    # These are PROTOTYPE thresholds for software demonstration.
    # They are NOT experimentally validated.
    # Adjust when real hardware and labeled data are available.

    IMPACT_THRESHOLD: float = 20.0          # m/s² magnitude
    TILT_THRESHOLD: float = 45.0            # degrees
    GYRO_THRESHOLD: float = 200.0           # deg/s magnitude
    DECELERATION_THRESHOLD: float = 15.0   # m/s² sudden change
    ACCIDENT_SCORE_THRESHOLD: float = 0.5   # 0.0–1.0

    # Severity thresholds
    SEVERITY_LOW_THRESHOLD: float = 0.3
    SEVERITY_MEDIUM_THRESHOLD: float = 0.5
    SEVERITY_HIGH_THRESHOLD: float = 0.7

    # Alcohol threshold
    ALCOHOL_THRESHOLD: float = 0.08         # BAC equivalent (0.08 = legal limit)

    # ── Temporary email alert (alcohol detected) ──────────────────────────────
    # Replaced later by the SIM800L SMS alert on the helmet.
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587                    # 587 = STARTTLS, 465 = SSL
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""                 # Gmail app password, set in .env only
    EMAIL_FROM: str = ""                    # defaults to SMTP_USER if empty
    EMAIL_TO: str = ""                      # comma-separated recipient addresses
    ALCOHOL_ALERT_INDEX: float = 0.10       # ESP32 alcohol index (0..1) that sends the email
    EMAIL_COOLDOWN_SECONDS: int = 120       # minimum gap between emails per rider
    EMAIL_ENCRYPT: bool = True
    EVIDENCE_KEY: str = ""  
    EMAIL_HISTORY_SECONDS: int = 10      
    EVIDENCE_ADMIN_TOKEN: str = ""          # access code for the Decrypt Alerts page; empty = page disabled   # how many seconds of readings go into each alert                # 64 hex chars (32-byte master key), keep secret

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()