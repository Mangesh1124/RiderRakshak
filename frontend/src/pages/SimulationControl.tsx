import React, { useState, useCallback } from 'react';
import { runSimulation } from '../services/api';
import type { SimulationResponse, Scenario } from '../types';
import { ScoreGauge, Badge, Spinner } from '../components/UI';
import CountdownAlert from '../components/CountdownAlert';
import type { Accident } from '../types';
import {
  classificationBadgeClass, severityBadgeClass,
  formatNum, formatTs
} from '../utils/helpers';

const SCENARIOS: { id: Scenario; label: string; icon: string; desc: string; className: string }[] = [
  { id: 'NORMAL', label: 'Normal Riding', icon: '🏍️', desc: 'Standard urban riding', className: 'normal' },
  { id: 'HARD_BRAKING', label: 'Hard Braking', icon: '🛑', desc: 'Sudden deceleration', className: 'hard-braking' },
  { id: 'SUDDEN_ACCELERATION', label: 'Sudden Accel', icon: '⚡', desc: 'Quick throttle', className: 'sudden-acc' },
  { id: 'HIGH_TILT', label: 'High Tilt', icon: '↗️', desc: 'Sharp cornering', className: 'high-tilt' },
  { id: 'FALL', label: 'Fall', icon: '💫', desc: 'Low-speed fall', className: 'fall' },
  { id: 'ACCIDENT', label: 'ACCIDENT', icon: '💥', desc: 'High-impact collision', className: 'accident' },
  { id: 'ALCOHOL_DETECTED', label: 'Alcohol Detected', icon: '🍺', desc: 'Rider impaired', className: 'alcohol' },
];

const SimulationControl: React.FC = () => {
  const [loading, setLoading] = useState<Scenario | null>(null);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingAccidentId, setPendingAccidentId] = useState<string | null>(null);
  const [resolvedAccident, setResolvedAccident] = useState<Accident | null>(null);

  const handleSimulate = useCallback(async (scenario: Scenario) => {
    setLoading(scenario);
    setError(null);
    setResult(null);
    setPendingAccidentId(null);
    setResolvedAccident(null);
    try {
      const res = await runSimulation(scenario, false);
      setResult(res);
      if (res.accident_id && res.accident_status === 'PENDING') {
        setPendingAccidentId(res.accident_id);
      }
    } catch (e: unknown) {
      setError('Simulation failed. Is the backend running?');
    } finally {
      setLoading(null);
    }
  }, []);

  const handleResolved = useCallback((acc: Accident) => {
    setPendingAccidentId(null);
    setResolvedAccident(acc);
  }, []);

  const feat = result?.features;
  const det = result?.detection_result;

  return (
    <div className="page-gap">
      <div className="alert-box info" style={{ fontSize: 12 }}>
        ⚡ <strong>SOFTWARE SIMULATION MODE</strong> — Click a scenario to run the full detection pipeline.
        Trigger <strong>ACCIDENT</strong> to test the complete end-to-end demonstration.
      </div>

      <div className="grid-2">
        {/* Scenario Buttons */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🎮 Scenario Control</div>
            {loading && <Spinner />}
          </div>
          <div className="scenario-grid">
            {SCENARIOS.map(s => (
              <button
                key={s.id}
                className={`scenario-btn ${s.className} ${loading === s.id ? 'loading' : ''}`}
                onClick={() => handleSimulate(s.id)}
                disabled={loading !== null}
              >
                <div className="scenario-icon">{loading === s.id ? '⏳' : s.icon}</div>
                <div className="scenario-name">{s.label}</div>
                <div className="scenario-desc">{s.desc}</div>
              </button>
            ))}
          </div>

          {error && <div className="alert-box danger" style={{ marginTop: 16 }}>{error}</div>}
        </div>

        {/* Result Panel */}
        <div>
          {/* Countdown Alert */}
          {pendingAccidentId && (
            <div style={{ marginBottom: 16 }}>
              <CountdownAlert
                accidentId={pendingAccidentId}
                onResolved={handleResolved}
              />
            </div>
          )}

          {/* Resolution */}
          {resolvedAccident && (
            <div className={`alert-box ${resolvedAccident.status === 'CONFIRMED_ACCIDENT' ? 'danger' : 'success'}`} style={{ marginBottom: 16 }}>
              {resolvedAccident.status === 'CONFIRMED_ACCIDENT' ? (
                <>
                  🚨 <strong>ACCIDENT CONFIRMED</strong><br />
                  ID: <span style={{ fontFamily: 'JetBrains Mono' }}>{resolvedAccident.id}</span><br />
                  Severity: <strong>{resolvedAccident.severity}</strong><br />
                  Simulated GSM alert sent. Check Accident Details for the full report.
                </>
              ) : (
                <>
                  ✅ <strong>FALSE ALERT CANCELLED</strong> by rider.<br />
                  Event preserved in database: <span style={{ fontFamily: 'JetBrains Mono' }}>{resolvedAccident.id}</span>
                </>
              )}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">📊 Pipeline Result</div>
                <Badge text={result.scenario} className="badge-pending" />
              </div>

              {/* Detection */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <Badge text={det?.classification ?? ''} className={classificationBadgeClass(det?.classification ?? '')} />
                  {result.detection_result.is_accident && (
                    <Badge text="⚠️ ACCIDENT DETECTED" className="badge-confirmed" />
                  )}
                </div>
                <ScoreGauge
                  score={det?.accident_score ?? 0}
                  breakdown={det?.score_breakdown}
                />
              </div>

              <hr className="sep" />

              {/* Features */}
              {feat && (
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Extracted Features</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                    {[
                      ['Acc Magnitude', `${formatNum(feat.acceleration_magnitude)} m/s²`],
                      ['Gyro Magnitude', `${formatNum(feat.gyro_magnitude)} °/s`],
                      ['Tilt Angle', `${formatNum(feat.tilt_angle, 1)}°`],
                      ['Deceleration', `${formatNum(feat.deceleration)} m/s²`],
                      ['Speed', `${formatNum(feat.speed, 1)} km/h`],
                      ['Alcohol', formatNum(feat.alcohol, 3)],
                    ].map(([k, v]) => (
                      <div key={k} style={{ padding: '8px 10px', background: 'var(--bg-700)', borderRadius: 6 }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{k}</div>
                        <div style={{ fontFamily: 'JetBrains Mono', fontWeight: 600, marginTop: 2 }}>{v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Alert Message */}
              {result.alert_message && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>System Message</div>
                  <div style={{ padding: '10px 12px', background: 'var(--bg-700)', borderRadius: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
                    {result.alert_message}
                  </div>
                </div>
              )}
            </div>
          )}

          {!result && !loading && (
            <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🎮</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                Select a scenario to run the simulation pipeline
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulationControl;
