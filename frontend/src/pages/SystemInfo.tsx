import React, { useEffect, useState } from 'react';
import { getSystemStatus, getSystemConfig } from '../services/api';
import type { SystemStatus } from '../types';
import { Spinner, InfoRow } from '../components/UI';
import { formatTs } from '../utils/helpers';

const SystemInfo: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getSystemStatus(), getSystemConfig()]).then(([s, c]) => {
      setStatus(s);
      setConfig(c);
      setLoading(false);
    });
    const t = setInterval(async () => { setStatus(await getSystemStatus()); }, 10000);
    return () => clearInterval(t);
  }, []);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spinner size={32} /></div>;

  const thresholds = config?.thresholds as Record<string, number> | undefined;

  return (
    <div className="page-gap">
      <div className="alert-box warning">
        ⚠️ <strong>Prototype Thresholds</strong> — All detection thresholds listed below are PROTOTYPE values for software demonstration.
        They are NOT experimentally validated. Calibrate with labeled real-world data when hardware is available.
      </div>

      <div className="grid-2">
        {/* System Status */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🖥️ System Status</div>
          <InfoRow label="App Name" value={status?.app_name ?? '—'} />
          <InfoRow label="Version" value={status?.version ?? '—'} />
          <InfoRow label="Environment" value={status?.environment ?? '—'} />
          <InfoRow label="Database" value={status?.database_status ?? '—'} />
          <InfoRow label="Active Rider" value={status?.active_rider ?? '—'} />
          <InfoRow label="Simulation Mode" value={status?.simulation_mode ? 'ENABLED' : 'DISABLED'} />
          <InfoRow label="Uptime" value={`${Math.floor((status?.uptime_seconds ?? 0) / 60)}m ${Math.floor((status?.uptime_seconds ?? 0) % 60)}s`} />
          <InfoRow label="Timestamp" value={formatTs(status?.timestamp ?? null)} />
        </div>

        {/* Hardware Status */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🔧 Hardware Status</div>
          {[
            ['ESP32', 'NOT_CONNECTED', 'Software simulator active'],
            ['MPU6050 (IMU)', 'NOT_CONNECTED', 'Simulated accelerometer + gyroscope'],
            ['GPS Module', 'NOT_CONNECTED', 'Simulated GPS coordinates'],
            ['GSM/LTE Module', 'NOT_CONNECTED', 'Simulated SMS alerts'],
            ['Alcohol Sensor', 'NOT_CONNECTED', 'Simulated BAC readings'],
          ].map(([hw, status, note]) => (
            <div key={hw} style={{ padding: '12px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{hw}</span>
                <span style={{ fontSize: 11, background: 'rgba(148,163,184,0.1)', color: '#94a3b8', padding: '2px 8px', borderRadius: 4 }}>
                  {status}
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{note}</div>
            </div>
          ))}
          <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(59,130,246,0.06)', borderRadius: 6, fontSize: 12, color: '#93c5fd' }}>
            📋 See <strong>docs/hardware_integration.md</strong> for connection instructions.
          </div>
        </div>
      </div>

      {/* Thresholds */}
      {thresholds && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 4 }}>⚙️ Detection Thresholds (Prototype)</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
            Configured in <span style={{ fontFamily: 'JetBrains Mono' }}>backend/app/config.py</span>.
            Override via environment variables or .env file.
          </div>
          <div className="grid-3">
            {Object.entries(thresholds).map(([k, v]) => (
              <div key={k} style={{ padding: '14px', background: 'var(--bg-700)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
                  {k.replace(/_threshold/i, '').replace(/_/g, ' ')}
                </div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: 20, fontWeight: 800, marginTop: 4 }}>
                  {v}
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)' }}>
            {config?.note as string}
          </div>
        </div>
      )}

      {/* Architecture note */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 12 }}>📐 Software Architecture</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8, fontFamily: 'JetBrains Mono', fontSize: 12, color: 'var(--text-secondary)' }}>
          {[
            'Sensor Simulator → SimulatedSensorProvider (base.py)',
            'Preprocessing → preprocess_reading() (preprocessing.py)',
            'Feature Extraction → extract_features() (features.py)',
            'Threshold Detection → detect_accident() (threshold_detector.py)',
            'Sensor Fusion → apply_sensor_fusion() (sensor_fusion.py)',
            'Severity → calculate_severity() (severity.py)',
            'False Alert → create_pending_accident() → cancel/confirm (alert_manager.py)',
            'GPS → SimulatedGPSProvider (gps.py)',
            'GSM → SimulatedGSMAdapter (gsm_simulator.py)',
            'Database → SQLAlchemy + SQLite → riderakshak.db',
            'API → FastAPI (main.py + routes/)',
            'Frontend → React + Vite + TypeScript',
          ].map((s, i) => (
            <div key={i} style={{ padding: '8px 12px', background: 'var(--bg-700)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: 'var(--accent-primary)', fontSize: 10 }}>▶</span>
              {s}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemInfo;
