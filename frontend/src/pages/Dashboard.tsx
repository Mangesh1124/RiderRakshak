import React, { useEffect, useState, useCallback } from 'react';
import { getSystemStatus, getAccidents, getLatestReading, getAlerts } from '../services/api';
import type { SystemStatus, AccidentListResponse, SensorReading, EmergencyAlert } from '../types';
import { MetricCard, ScoreGauge, Badge, Spinner, SimBadge } from '../components/UI';
import {
  formatTs, formatNum, classificationBadgeClass,
  statusBadgeClass, severityBadgeClass, scoreColor
} from '../utils/helpers';

const Dashboard: React.FC = () => {
  const [system, setSystem] = useState<SystemStatus | null>(null);
  const [accidents, setAccidents] = useState<AccidentListResponse | null>(null);
  const [latest, setLatest] = useState<SensorReading | null>(null);
  const [alerts, setAlerts] = useState<EmergencyAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [sys, acc, lat, alts] = await Promise.all([
        getSystemStatus(),
        getAccidents(10),
        getLatestReading(),
        getAlerts(5),
      ]);
      setSystem(sys);
      setAccidents(acc);
      setLatest(lat);
      setAlerts(alts);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 5000);
    return () => clearInterval(t);
  }, [fetchAll]);

  const pendingCount = accidents?.accidents.filter(a => a.status === 'PENDING').length ?? 0;
  const confirmedCount = accidents?.accidents.filter(a => a.status === 'CONFIRMED_ACCIDENT').length ?? 0;

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
      <Spinner size={32} />
    </div>
  );

  return (
    <div className="page-gap">
      {/* Status Banner */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))',
        border: '1px solid rgba(59,130,246,0.2)', borderRadius: 'var(--radius-lg)', padding: '16px 24px',
      }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>🏍️ RideRakshak Dashboard</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
            IoT-Based Smart Helmet — Software MVP v{system?.version}
          </div>
          <SimBadge />
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>DB Status</div>
            <div style={{ fontWeight: 700, color: system?.database_status === 'OK' ? '#10b981' : '#ef4444' }}>
              {system?.database_status ?? '—'}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Uptime</div>
            <div style={{ fontFamily: 'JetBrains Mono', fontWeight: 700 }}>
              {Math.floor((system?.uptime_seconds ?? 0) / 60)}m {Math.floor((system?.uptime_seconds ?? 0) % 60)}s
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Active Rider</div>
            <div style={{ fontWeight: 700, fontFamily: 'JetBrains Mono' }}>{system?.active_rider}</div>
          </div>
        </div>
      </div>

      {/* Alert Banner for pending */}
      {pendingCount > 0 && (
        <div className="alert-box danger" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 20 }}>🚨</span>
          <div>
            <strong>{pendingCount} PENDING ACCIDENT ALERT{pendingCount > 1 ? 'S' : ''}</strong> — Awaiting confirmation or cancellation.
            <br />
            <span style={{ fontSize: 12, opacity: 0.8 }}>Go to Simulation Control to respond within the cancellation window.</span>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid-4">
        <MetricCard
          label="Total Accidents"
          value={accidents?.total ?? 0}
          accent="blue"
          icon="💥"
          sub="All recorded events"
        />
        <MetricCard
          label="Pending Alerts"
          value={pendingCount}
          accent={pendingCount > 0 ? 'red' : 'green'}
          icon="⚠️"
          sub="Awaiting response"
        />
        <MetricCard
          label="Confirmed"
          value={confirmedCount}
          accent="red"
          icon="🚑"
          sub="Emergency alerts sent"
        />
        <MetricCard
          label="Current Speed"
          value={formatNum(latest?.speed, 1)}
          unit="km/h"
          accent="cyan"
          icon="🚀"
        />
      </div>

      {/* Sensor Snapshot + Score */}
      <div className="grid-2">
        {/* Latest Sensor Reading */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">📡 Latest Sensor Reading</div>
            {latest && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
                {formatTs(latest.timestamp)}
              </span>
            )}
          </div>
          {latest ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>Accelerometer (m/s²)</div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: 13, lineHeight: 2 }}>
                  <span style={{ color: '#ef4444' }}>X</span> {formatNum(latest.accel_x)}&nbsp;
                  <span style={{ color: '#10b981' }}>Y</span> {formatNum(latest.accel_y)}&nbsp;
                  <span style={{ color: '#3b82f6' }}>Z</span> {formatNum(latest.accel_z)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10, marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Gyroscope (°/s)</div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: 13, lineHeight: 2 }}>
                  <span style={{ color: '#ef4444' }}>X</span> {formatNum(latest.gyro_x)}&nbsp;
                  <span style={{ color: '#10b981' }}>Y</span> {formatNum(latest.gyro_y)}&nbsp;
                  <span style={{ color: '#3b82f6' }}>Z</span> {formatNum(latest.gyro_z)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>Derived</div>
                <div style={{ lineHeight: 2.2, fontSize: 13 }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>Acc Mag: </span><span style={{ fontFamily: 'JetBrains Mono', color: '#f59e0b' }}>{formatNum(latest.acceleration_magnitude)} m/s²</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Gyro Mag: </span><span style={{ fontFamily: 'JetBrains Mono', color: '#8b5cf6' }}>{formatNum(latest.gyro_magnitude)} °/s</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Tilt: </span><span style={{ fontFamily: 'JetBrains Mono', color: '#06b6d4' }}>{formatNum(latest.tilt_angle)}°</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Alcohol: </span><span style={{ fontFamily: 'JetBrains Mono', color: latest.alcohol > 0.08 ? '#ef4444' : '#10b981' }}>{formatNum(latest.alcohol, 3)}</span></div>
                </div>
              </div>
              <div style={{ gridColumn: '1/-1' }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>GPS (Simulated)</div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#10b981' }}>
                  📍 {formatNum(latest.latitude, 6)}, {formatNum(latest.longitude, 6)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Scenario: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{latest.scenario}</span>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '20px 0', textAlign: 'center' }}>
              No sensor readings yet — run a simulation
            </div>
          )}
        </div>

        {/* Recent Accidents */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🚨 Recent Accident Events</div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Last 10</span>
          </div>
          {(accidents?.accidents.length ?? 0) === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: '20px 0', textAlign: 'center' }}>
              No accidents recorded
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {accidents!.accidents.slice(0, 6).map(acc => (
                <div key={acc.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 12px', background: 'var(--bg-700)', borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                }}>
                  <div>
                    <div style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: 'var(--text-secondary)' }}>{acc.id}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{formatTs(acc.timestamp)}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    {acc.severity && <Badge text={acc.severity} className={severityBadgeClass(acc.severity)} />}
                    <Badge text={acc.status.replace('_', ' ')} className={statusBadgeClass(acc.status)} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Emergency Alerts */}
      {alerts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📡 Recent Simulated GSM Alerts</div>
            <span style={{ fontSize: 11, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', padding: '2px 8px', borderRadius: 4 }}>
              SIMULATED — No real SMS sent
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {alerts.map(a => (
              <div key={a.id} style={{
                padding: '10px 14px', background: 'var(--bg-700)', borderRadius: 8,
                border: '1px solid rgba(239,68,68,0.15)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono', color: 'var(--text-secondary)' }}>
                    Accident: {a.accident_id}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{formatTs(a.timestamp)}</span>
                </div>
                <div style={{ fontSize: 12, color: '#fca5a5', fontWeight: 600 }}>
                  {a.alert_type} | Status: {a.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
