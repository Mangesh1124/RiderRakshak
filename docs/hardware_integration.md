# Hardware Integration Guide

## Overview

This document describes how to replace the software simulators with
real hardware components when they become available.

**Current state:** All hardware is simulated in software.  
**Future state:** ESP32 + MPU6050 + GPS + GSM + Alcohol sensor.

---

## Architecture Comparison

### Current (Software Simulation)
```
SimulatedSensorProvider
        ↓
SensorReading (dataclass)
        ↓
preprocessing.py → features.py → threshold_detector.py
        ↓
sensor_fusion.py → severity.py → alert_manager.py
        ↓
SimulatedGSMAdapter → SQLite → FastAPI → React
```

### Future (Hardware)
```
ESP32 + MPU6050 (I2C)
        ↓
Firmware reads IMU @ 100Hz
        ↓
ESP32 WiFi/Serial → HTTP POST → /api/sensors/ingest (new endpoint)
        ↓
HardwareSensorProvider (implements SensorProvider)
        ↓
[Same pipeline — no changes to detection code]
        ↓
HardwareGSMAdapter → SIM800L AT commands → Real SMS
```

---

## Step-by-Step Hardware Integration

### 1. Replace SimulatedSensorProvider

File: `backend/app/sensors/base.py`

```python
class HardwareSensorProvider(SensorProvider):
    """Reads from ESP32 via HTTP or serial."""
    
    def get_reading(self, scenario=None) -> SensorReading:
        # Option A: Poll ESP32 HTTP endpoint
        import requests
        data = requests.get("http://esp32.local/sensor").json()
        return SensorReading(
            timestamp=datetime.utcnow(),
            accelerometer=AccelerometerReading(
                x=data["ax"], y=data["ay"], z=data["az"]
            ),
            gyroscope=GyroscopeReading(
                x=data["gx"], y=data["gy"], z=data["gz"]
            ),
            gps=GPSReading(lat=data["lat"], lon=data["lon"]),
            alcohol=data["alcohol"],
            speed=data["speed"],
            scenario="HARDWARE",
        )
```

### 2. Replace SimulatedGPSProvider

File: `backend/app/sensors/gps.py`

```python
class HardwareGPSProvider(GPSProvider):
    def get_location(self) -> GPSReading:
        # Read from NMEA serial stream or ESP32 HTTP
        ...
```

### 3. Replace SimulatedGSMAdapter

File: `backend/app/emergency/gsm_simulator.py`

```python
class HardwareGSMAdapter(GSMAdapter):
    def send_alert(self, payload: AlertPayload) -> AlertResult:
        # Send AT commands to SIM800L via ESP32 serial
        message = f"ACCIDENT: {payload.severity} at {payload.latitude},{payload.longitude}"
        # at_command("AT+CMGS", payload.emergency_contact, message)
        ...
```

---

## ESP32 Firmware Notes

The ESP32 firmware should:
1. Read MPU6050 via I2C at 100Hz
2. Apply low-pass filter (avoid single-spike false triggers)
3. POST sensor data to `/api/sensors/ingest` every 100ms
4. OR expose `/sensor` endpoint for polling

Suggested library: `Wire.h` + `MPU6050.h` for Arduino framework.

---

## MPU6050 → Feature Schema Mapping

| MPU6050 Output | Feature Schema | Units |
|----------------|----------------|-------|
| Accel X | accel_x | m/s² (divide raw by 16384 × 9.81) |
| Accel Y | accel_y | m/s² |
| Accel Z | accel_z | m/s² |
| Gyro X | gyro_x | deg/s (divide raw by 131) |
| Gyro Y | gyro_y | deg/s |
| Gyro Z | gyro_z | deg/s |

---

## Threshold Calibration

After collecting real hardware data with known events:

1. Record labeled sessions: NORMAL / HARD_BRAKING / ACCIDENT
2. Run feature extraction on all recordings
3. Analyze distributions to set empirically validated thresholds
4. Update `backend/app/config.py`:
   ```
   IMPACT_THRESHOLD = <calibrated_value>
   TILT_THRESHOLD = <calibrated_value>
   ```

---

## Future: Video Evidence Module

Planned (NOT in current MVP):
- ESP32-CAM circular buffer (pre-impact)
- AES-GCM encryption of video frames
- HMAC-SHA256 tamper detection
- Cloud upload on accident confirmation

This module will be added in a future development phase.

---

## Summary Checklist

- [ ] ESP32 firmware reads MPU6050
- [ ] ESP32 exposes sensor HTTP endpoint
- [ ] Implement HardwareSensorProvider
- [ ] Implement HardwareGPSProvider
- [ ] Implement HardwareGSMAdapter
- [ ] Calibrate detection thresholds with real data
- [ ] Collect labeled accident dataset for ML training
- [ ] Migrate database to PostgreSQL for production
- [ ] Add sliding-window feature extraction
- [ ] Deploy to cloud (future)
