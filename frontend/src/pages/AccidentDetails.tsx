import React, { useEffect, useState } from 'react';
import { getAccident, getAccidentAlerts, cancelAccident, confirmAccident } from '../services/api';
import type { Accident, EmergencyAlert } from '../types';
import { ScoreGauge, Badge, Spinner, InfoRow } from '../components/UI';
import {
  formatTs, formatNum, statusBadgeClass,
  severityBadgeClass, classificationBadgeClass
} from '../utils/helpers';

interface AccidentDetailsProps {
  accidentId: string;
  onBack?: () => void;
}

const AccidentDetails: React.FC<AccidentDetailsProps> = ({ accidentId, onBack }) => {
  const [accident, setAccident] = useState<Accident | null>(null);
  const [alerts, setAlerts] = useState<EmergencyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  const fetchData = async () => {
    const [acc, alts] = await Promise.all([
      getAccident(accidentId),
      getAccidentAlerts(accidentId),
    ]);
    setAccident(acc);
    setAlerts(alts);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [accidentId]);

  const handleCancel = async () => {
    setActing(true);
    try { const a = await cancelAccident(accidentId); setAccident(a); } finally { setActing(false); }
  };

  const handleConfirm = async () => {
    setActing(true);
    try { const a = await confirmAccident(accidentId); setAccident(a); await fetchData(); } finally { setActing(false); }
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spinner size={32} /></div>;
  if (!accident) return <div style={{ padding: 40, color: 'var(--text-muted)' }}>Accident not found.</div>;

  const features = accident.features_snapshot as Record<string, unknown> | null;
  const breakdown = accident.score_breakdown as Record<string, unknown> | null;

  return (
    <div className="page-gap">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {onBack && (
          <button className="btn btn-ghost btn-sm" onClick={onBack}>← Back</button>
        )}
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>Accident Details</div>
          <div style={{ fontFamily: 'JetBrains Mono', fontSize: 20, fontWeight: 800 }}>{accident.id}</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <Badge text={accident.status.replace(/_/g, ' ')} className={statusBadgeClass(accident.status)} />
          {accident.severity && <Badge text={accident.severity} className={severityBadgeClass(accident.severity)} />}
        </div>
      </div>

      {/* Actions for PENDING */}
      {accident.status === 'PENDING' && (
        <div className="alert-box danger">
          <strong>⚠️ PENDING — Awaiting Response</strong>
          <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
            <button className="btn btn-danger" onClick={handleCancel} disabled={acting}>
              {acting ? '⏳' : '✋'} Cancel (False Alert)
            </button>
            <button className="btn btn-success" onClick={handleConfirm} disabled={acting}>
              {acting ? '⏳' : '✅'} Confirm Accident
            </button>
          </div>
        </div>
      )}

      {accident.status === 'CONFIRMED_ACCIDENT' && (
        <div className="alert-box danger">
          🚨 <strong>ACCIDENT CONFIRMED</strong> — Simulated emergency alert generated.
        </div>
      )}
      {accident.status === 'FALSE_ALERT_CANCELLED' && (
        <div className="alert-box success">
          ✅ <strong>FALSE ALERT CANCELLED</strong> by rider. Event preserved for review.
        </div>
      )}

      <div className="grid-2">
        {/* Info */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>📋 Accident Information</div>
          <InfoRow label="Accident ID" value={accident.id} />
          <InfoRow label="Rider ID" value={accident.rider_id} />
          <InfoRow label="Timestamp" value={formatTs(accident.timestamp)} />
          <InfoRow label="Classification" value={accident.classification.replace(/_/g, ' ')} />
          <InfoRow label="Severity" value={accident.severity ?? '—'} />
          <InfoRow label="Status" value={accident.status.replace(/_/g, ' ')} />
          {accident.confirmed_at && <InfoRow label="Confirmed At" value={formatTs(accident.confirmed_at)} />}
          {accident.cancelled_at && <InfoRow label="Cancelled At" value={formatTs(accident.cancelled_at)} />}
          <InfoRow label="Latitude" value={accident.latitude != null ? formatNum(accident.latitude, 6) : '—'} />
          <InfoRow label="Longitude" value={accident.longitude != null ? formatNum(accident.longitude, 6) : '—'} />
          {accident.latitude && (
            <div style={{ marginTop: 12 }}>
              <a
                href={`https://maps.google.com/?q=${accident.latitude},${accident.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm"
              >
                📍 Open in Maps (Simulated Location)
              </a>
            </div>
          )}
        </div>

        {/* Score */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>📊 Accident Score</div>
          <ScoreGauge
            score={accident.accident_score}
            breakdown={breakdown as Record<string, number>}
          />
          <hr className="sep" />
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Score Breakdown Note</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Impact, tilt, rotation, and deceleration components contribute to the total accident score.
            Fusion rules may boost or dampen the final score.
          </div>
        </div>
      </div>

      {/* Features */}
      {features && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🔬 Extracted Features (at time of detection)</div>
          <div className="grid-4">
            {([
              ['Acc Magnitude', formatNum(features.acceleration_magnitude as number), 'm/s²'],
              ['Gyro Magnitude', formatNum(features.gyro_magnitude as number), '°/s'],
              ['Tilt Angle', formatNum(features.tilt_angle as number, 1), '°'],
              ['Peak Acceleration', formatNum(features.peak_acceleration as number), 'm/s²'],
              ['Peak Gyro', formatNum(features.peak_gyro as number), '°/s'],
              ['Deceleration', formatNum(features.deceleration as number), 'm/s²'],
              ['Speed', formatNum(features.speed as number, 1), 'km/h'],
              ['Alcohol', formatNum(features.alcohol as number, 3), 'BAC equiv.'],
            ] as [string, string, string][]).map(([k, v, u]) => (
              <div key={k} style={{ padding: '12px 14px', background: 'var(--bg-700)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>{k}</div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: 16, fontWeight: 700, marginTop: 4 }}>{v}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{u}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GSM Alert */}
      {alerts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📡 Simulated GSM Emergency Alert</div>
            <span style={{ fontSize: 11, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', padding: '2px 8px', borderRadius: 4 }}>
              NO REAL SMS SENT
            </span>
          </div>
          {alerts.map(a => (
            <div key={a.id}>
              <div className="gsm-alert-box">{a.message}</div>
              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                Type: {a.alert_type} | Status: {a.status} | {formatTs(a.timestamp)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AccidentDetails;
