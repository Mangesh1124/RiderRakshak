// RideRakshak TypeScript Types

export interface AccelerometerData {
  x: number;
  y: number;
  z: number;
}

export interface GyroscopeData {
  x: number;
  y: number;
  z: number;
}

export interface GPSData {
  latitude: number;
  longitude: number;
}

export interface SensorReading {
  id: number;
  rider_id: string;
  timestamp: string;
  scenario: string;
  accel_x: number;
  accel_y: number;
  accel_z: number;
  gyro_x: number;
  gyro_y: number;
  gyro_z: number;
  acceleration_magnitude: number | null;
  gyro_magnitude: number | null;
  tilt_angle: number | null;
  alcohol: number;
  latitude: number | null;
  longitude: number | null;
  speed: number;
}

export interface ExtractedFeatures {
  acceleration_magnitude: number;
  gyro_magnitude: number;
  tilt_angle: number;
  peak_acceleration: number;
  peak_gyro: number;
  angular_velocity: number;
  deceleration: number;
  speed: number;
  alcohol: number;
  scenario: string;
}

export interface DetectionResult {
  classification: string;
  accident_score: number;
  score_breakdown: Record<string, number>;
  is_accident: boolean;
  features: ExtractedFeatures;
}

export interface Accident {
  id: string;
  rider_id: string;
  timestamp: string;
  accident_score: number;
  classification: string;
  severity: string | null;
  status: string;
  cancellation_deadline: string | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
  latitude: number | null;
  longitude: number | null;
  sensor_snapshot: Record<string, unknown> | null;
  features_snapshot: Record<string, unknown> | null;
  score_breakdown: Record<string, unknown> | null;
}

export interface AccidentListResponse {
  total: number;
  accidents: Accident[];
}

export interface EmergencyAlert {
  id: number;
  accident_id: string;
  timestamp: string;
  alert_type: string;
  status: string;
  recipient: string | null;
  message: string;
}

export interface SystemStatus {
  app_name: string;
  version: string;
  environment: string;
  simulation_mode: boolean;
  database_status: string;
  active_rider: string;
  uptime_seconds: number;
  timestamp: string;
}

export interface SimulationResponse {
  scenario: string;
  sensor_reading: {
    timestamp: string;
    accelerometer: AccelerometerData;
    gyroscope: GyroscopeData;
    alcohol: number;
    gps: GPSData;
    speed: number;
    scenario: string;
  };
  features: ExtractedFeatures;
  detection_result: DetectionResult;
  accident_id: string | null;
  accident_status: string | null;
  alert_message: string | null;
  message: string;
}

export type Scenario =
  | 'NORMAL'
  | 'HARD_BRAKING'
  | 'SUDDEN_ACCELERATION'
  | 'HIGH_TILT'
  | 'FALL'
  | 'ACCIDENT'
  | 'ALCOHOL_DETECTED';

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AccidentStatus = 'PENDING' | 'CONFIRMED_ACCIDENT' | 'FALSE_ALERT_CANCELLED';
