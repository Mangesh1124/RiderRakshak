# RideRakshak — IoT-Based Smart Helmet
## Software MVP v1.0

> **Academic Project** | IoT-Based Smart Helmet with Secure Sensor Logs  
> and Pre-Impact Video Evidence Using Machine Learning Approaches  
>  
> ⚡ **SOFTWARE PROTOTYPE — No physical hardware required**  
> 🔬 **SIMULATION MODE — All sensor data is synthetically generated**

---

## Overview

RideRakshak is a software-only MVP that simulates the complete pipeline of an IoT smart helmet system:

```
Sensor Simulator → Preprocessing → Feature Extraction → 
Accident Detection → Sensor Fusion → Severity → 
False Alert Cancellation → GPS → GSM Alert → Database → API → Dashboard
```

No physical hardware (ESP32, MPU6050, GPS, GSM) is required for this version.  
The architecture is designed for easy hardware integration in a future phase.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (PostgreSQL-ready) |
| ML | scikit-learn, NumPy, Pandas |
| Frontend | React 18, Vite, TypeScript |
| Charts | Recharts |

---

## Project Structure

```
RideRakshak/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # All configurable settings
│   │   ├── api/routes/
│   │   │   ├── simulation.py          # POST /api/simulation/{scenario}
│   │   │   ├── accidents.py           # Accident CRUD + cancel/confirm
│   │   │   ├── sensors.py             # Sensor history
│   │   │   ├── alerts.py              # Emergency alert log
│   │   │   └── system.py              # System status + config
│   │   ├── database/
│   │   │   ├── database.py            # SQLAlchemy engine + session
│   │   │   ├── models.py              # ORM models
│   │   │   └── schemas.py             # Pydantic schemas
│   │   ├── sensors/
│   │   │   ├── base.py                # Abstract SensorProvider interface
│   │   │   ├── simulator.py           # SimulatedSensorProvider (7 scenarios)
│   │   │   └── gps.py                 # SimulatedGPSProvider
│   │   ├── accident/
│   │   │   ├── preprocessing.py       # Sensor data cleaning
│   │   │   ├── features.py            # Feature extraction
│   │   │   ├── threshold_detector.py  # Threshold-based detection
│   │   │   ├── sensor_fusion.py       # Multi-sensor fusion
│   │   │   ├── severity.py            # Severity classification
│   │   │   └── ml_detector.py         # ML model pipeline
│   │   ├── emergency/
│   │   │   ├── gsm_simulator.py       # Simulated GSM adapter
│   │   │   └── alert_manager.py       # Alert lifecycle management
│   │   └── services/
│   │       └── accident_id.py         # Unique accident ID generation
│   ├── tests/
│   │   ├── test_simulation.py
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── LiveSensors.tsx
│       │   ├── SimulationControl.tsx
│       │   ├── AccidentEvents.tsx
│       │   ├── AccidentDetails.tsx
│       │   └── SystemInfo.tsx
│       ├── components/
│       │   ├── UI.tsx
│       │   └── CountdownAlert.tsx
│       └── services/api.ts
├── ml/
│   └── training/train.py              # ML pipeline
└── docs/
    ├── architecture.md
    ├── api.md
    ├── ml.md
    └── hardware_integration.md
```

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### 1. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

Dashboard available at: **http://localhost:5173**

---

## Simulation Instructions

### Primary MVP Demonstration

1. Open **http://localhost:5173**
2. Go to **Simulation Control**
3. Click **🏍️ Normal Riding** — observe zero accident score
4. Click **💥 ACCIDENT** — observe:
   - High acceleration magnitude (~30 m/s²)
   - High gyroscope magnitude (~300 °/s)
   - Tilt angle ~85°
   - Accident score > 0.5
   - Accident ID generated: `RR-ACC-YYYYMMDD-XXXX`
   - **10-second cancellation countdown**
5. Either:
   - Click **Cancel** → `FALSE_ALERT_CANCELLED` (event preserved in DB)
   - Wait → `CONFIRMED_ACCIDENT` + simulated GSM alert
6. View accident details, GSM message, GPS coordinates
7. Check **Accident Events** for full history

### API Direct Simulation

```bash
# Normal
curl -X POST http://localhost:8000/api/simulation/normal

# Accident
curl -X POST http://localhost:8000/api/simulation/accident

# Cancel accident
curl -X POST http://localhost:8000/api/accidents/RR-ACC-20260925-0001/cancel

# Confirm accident
curl -X POST http://localhost:8000/api/accidents/RR-ACC-20260925-0001/confirm
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/status` | System status |
| GET | `/api/system/status` | Full status + uptime |
| GET | `/api/system/config` | Threshold configuration |
| POST | `/api/simulation/{scenario}` | Run simulation pipeline |
| GET | `/api/simulation/scenarios` | List valid scenarios |
| GET | `/api/sensors/latest` | Latest sensor reading |
| GET | `/api/sensors/history` | Sensor reading history |
| GET | `/api/accidents` | List accidents |
| GET | `/api/accidents/{id}` | Get accident by ID |
| POST | `/api/accidents/{id}/cancel` | Cancel (false alert) |
| POST | `/api/accidents/{id}/confirm` | Confirm accident |
| GET | `/api/accidents/{id}/alerts` | Get alerts for accident |
| GET | `/api/alerts` | List all alerts |

**Valid Scenarios:** `NORMAL`, `HARD_BRAKING`, `SUDDEN_ACCELERATION`, `HIGH_TILT`, `FALL`, `ACCIDENT`, `ALCOHOL_DETECTED`

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

**38 tests — all must pass.**

Test coverage:
- Sensor simulation (all 7 scenarios)
- Preprocessing (clamp, NaN handling)
- Feature extraction (formula verification)
- Accident detection (normal = no accident, accident = detected)
- Sensor fusion (score range, notes)
- Severity classification
- False alert cancellation flow
- Accident confirmation flow
- All API endpoints

---

## ML Pipeline

```bash
# Generate synthetic demo dataset and train (SOFTWARE DEMO ONLY)
cd ml/training
python train.py --generate-demo --model random_forest

# Train on real dataset (when available)
python train.py --dataset /path/to/real_imu_dataset.csv --model random_forest
```

> ⚠️ **Academic Integrity Note:** No real IMU/accident dataset is bundled.
> Do NOT claim model accuracy without training on real labeled data.
> The `--generate-demo` flag trains on SIMULATED data only.

---

## Accident Detection Thresholds

| Parameter | Default | Unit | Note |
|-----------|---------|------|------|
| IMPACT_THRESHOLD | 20.0 | m/s² | Acceleration magnitude |
| TILT_THRESHOLD | 45.0 | degrees | Lean angle |
| GYRO_THRESHOLD | 200.0 | deg/s | Angular velocity |
| DECELERATION_THRESHOLD | 15.0 | m/s² | Braking force |
| ACCIDENT_SCORE_THRESHOLD | 0.5 | 0–1 | Final trigger |
| ALCOHOL_THRESHOLD | 0.08 | BAC equiv. | Legal limit |

> ⚠️ **PROTOTYPE THRESHOLDS — Not experimentally validated.**
> Calibrate with labeled real-world data when hardware is available.

Configure via `.env` or environment variables.

---

## Current Limitations

1. **No physical hardware** — all sensors simulated
2. **No real GPS** — coordinates are near a fixed base location with small Gaussian drift
3. **No real GSM** — emergency alerts are logged, not transmitted
4. **Single-reading detection** — no sliding window; window-based features planned
5. **No ML model** — ML pipeline structure exists; training requires real dataset
6. **SQLite** — suitable for MVP; PostgreSQL migration needed for production
7. **Prototype thresholds** — not experimentally calibrated
8. **No video evidence** — out of scope for this version

---

## Out-of-Scope Features (Future Phase)

The following are planned but NOT implemented:
- Pre-impact video buffering / ESP32-CAM
- AES-GCM encryption of sensor logs
- HMAC-SHA256 tamper detection
- Cloud evidence storage
- Video evidence verification

See: `docs/hardware_integration.md`

---

## Academic Integrity

This is an academic/IEEE project prototype.

**We do NOT claim:**
- Validated accident detection accuracy
- Real GPS accuracy
- Real SMS delivery
- Clinical injury prediction
- Hardware-tested results

All results are from **SOFTWARE SIMULATION**.

---

## Team

Academic Project — IoT Systems / Embedded ML  
© 2026 | RideRakshak v1.0.0-mvp
