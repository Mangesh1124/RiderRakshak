// API Service — communicates with FastAPI backend
import axios from 'axios';
import type {
  SensorReading,
  Accident,
  AccidentListResponse,
  EmergencyAlert,
  SystemStatus,
  SimulationResponse,
  Scenario,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () => api.get('/api/health').then(r => r.data);

// ── System ────────────────────────────────────────────────────────────────────
export const getSystemStatus = (): Promise<SystemStatus> =>
  api.get('/api/system/status').then(r => r.data);

export const getSystemConfig = () =>
  api.get('/api/system/config').then(r => r.data);

// ── Sensors ───────────────────────────────────────────────────────────────────
export const getLatestReading = (): Promise<SensorReading | null> =>
  api.get('/api/sensors/latest').then(r => r.data);

export const getSensorHistory = (limit = 100): Promise<{ total: number; readings: SensorReading[] }> =>
  api.get(`/api/sensors/history?limit=${limit}`).then(r => r.data);

// ── Accidents ─────────────────────────────────────────────────────────────────
export const getAccidents = (limit = 50): Promise<AccidentListResponse> =>
  api.get(`/api/accidents?limit=${limit}`).then(r => r.data);

export const getAccident = (id: string): Promise<Accident> =>
  api.get(`/api/accidents/${id}`).then(r => r.data);

export const cancelAccident = (id: string): Promise<Accident> =>
  api.post(`/api/accidents/${id}/cancel`).then(r => r.data);

export const confirmAccident = (id: string): Promise<Accident> =>
  api.post(`/api/accidents/${id}/confirm`).then(r => r.data);

export const getAccidentAlerts = (id: string): Promise<EmergencyAlert[]> =>
  api.get(`/api/accidents/${id}/alerts`).then(r => r.data);

// ── Alerts ────────────────────────────────────────────────────────────────────
export const getAlerts = (limit = 50): Promise<EmergencyAlert[]> =>
  api.get(`/api/alerts?limit=${limit}`).then(r => r.data);

// ── Simulation ────────────────────────────────────────────────────────────────
export const runSimulation = (
  scenario: Scenario,
  autoConfirm = false,
): Promise<SimulationResponse> =>
  api.post(`/api/simulation/${scenario}?auto_confirm=${autoConfirm}`).then(r => r.data);

export const getScenarios = (): Promise<{ scenarios: Scenario[]; mode: string }> =>
  api.get('/api/simulation/scenarios').then(r => r.data);

export default api;
