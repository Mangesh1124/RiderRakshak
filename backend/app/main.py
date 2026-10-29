"""
RideRakshak — FastAPI Backend Entry Point

Software MVP v1.0
IoT-Based Smart Helmet with Secure Sensor Logs
and Pre-Impact Video Evidence Using Machine Learning Approaches

NOTE: SOFTWARE SIMULATION MODE — No physical hardware connected.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.database import init_db
from app.api.routes import (
    simulation, accidents, sensors, alerts, system, ingest, notifications, evidence,
)

# ── Logging Configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App Lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and log startup."""
    logger.info("=" * 60)
    logger.info("  RideRakshak Backend Starting")
    logger.info("  Version: %s", settings.APP_VERSION)
    logger.info("  Environment: %s", settings.APP_ENV)
    logger.info("  Database: %s", settings.DATABASE_URL)
    logger.info("  Simulation Mode: %s", settings.SIMULATION_MODE)
    logger.info("=" * 60)

    init_db()
    _ensure_default_rider()

    logger.info("Backend ready.")
    yield
    logger.info("RideRakshak Backend shutting down.")


def _ensure_default_rider():
    """Create default test rider if not exists."""
    from app.database.database import SessionLocal
    from app.database.models import Rider
    db = SessionLocal()
    try:
        rider = db.query(Rider).filter(Rider.id == settings.DEFAULT_RIDER_ID).first()
        if not rider:
            rider = Rider(
                id=settings.DEFAULT_RIDER_ID,
                name="Test Rider (MVP)",
                phone="+91-0000000000",
                emergency_contact="Emergency Contact Pending",
            )
            db.add(rider)
            db.commit()
            logger.info("Default rider created: %s", settings.DEFAULT_RIDER_ID)
    finally:
        db.close()


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="RideRakshak API",
    description=(
        "IoT-Based Smart Helmet Software MVP — Sensor simulation, "
        "accident detection, and emergency alert system. "
        "SOFTWARE SIMULATION MODE."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(simulation.router)
app.include_router(accidents.router)
app.include_router(sensors.router)
app.include_router(alerts.router)
app.include_router(system.router)
app.include_router(ingest.router)
app.include_router(notifications.router)
app.include_router(evidence.router)

# ── Health & Root ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "mode": "SOFTWARE_SIMULATION",
        "version": settings.APP_VERSION,
    }


@app.get("/api/status")
def status():
    return {
        "status": "running",
        "simulation_mode": True,
        "hardware": "NOT_CONNECTED",
        "note": "SOFTWARE PROTOTYPE — Hardware integration pending",
    }


@app.get("/")
def root():
    return {
        "name": "RideRakshak API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "mode": "SOFTWARE_SIMULATION",
    }