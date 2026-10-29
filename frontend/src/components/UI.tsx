import React from 'react';
import { scoreColor, severityColor, formatNum } from '../utils/helpers';

// ── Metric Card ───────────────────────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  accent?: string;
  icon?: string;
  sub?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, accent = 'blue', icon, sub }) => (
  <div className={`metric-card accent-${accent}`}>
    <div className="metric-label">{icon && <span>{icon}</span>}{label}</div>
    <div className="metric-value">{value}</div>
    {unit && <div className="metric-sub">{unit}</div>}
    {sub && <div className="metric-sub">{sub}</div>}
  </div>
);

// ── Score Gauge ───────────────────────────────────────────────────────────────
interface ScoreGaugeProps {
  score: number;
  label?: string;
  showBreakdown?: boolean;
  breakdown?: Record<string, number>;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ score, label = 'Accident Score', breakdown }) => {
  const color = scoreColor(score);
  const pct = Math.round(score * 100);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 22, fontWeight: 800, color }}>{pct}%</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      {breakdown && (
        <div style={{ marginTop: 12 }}>
          {Object.entries(breakdown).filter(([k]) => typeof breakdown[k] === 'number').map(([k, v]) => (
            <div className="breakdown-row" key={k}>
              <div className="breakdown-key">{k.replace(/_/g, ' ')}</div>
              <div className="breakdown-track">
                <div className="breakdown-fill" style={{ width: `${Math.min(100, (v as number) * 1000)}%` }} />
              </div>
              <div className="breakdown-val">{formatNum(v as number, 3)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Axis Bar ─────────────────────────────────────────────────────────────────
interface AxisBarProps {
  label: string;
  value: number;
  max: number;
  color?: string;
  unit?: string;
}

export const AxisBar: React.FC<AxisBarProps> = ({ label, value, max, color = '#3b82f6', unit = '' }) => {
  const absVal = Math.abs(value);
  const pct = Math.min(100, (absVal / max) * 100);
  return (
    <div className="axis-row">
      <div className="axis-label">{label}</div>
      <div className="axis-bar-track">
        <div className="axis-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="axis-value">{value.toFixed(2)}{unit}</div>
    </div>
  );
};

// ── Badge ─────────────────────────────────────────────────────────────────────
interface BadgeProps {
  text: string;
  className?: string;
}
export const Badge: React.FC<BadgeProps> = ({ text, className = '' }) => (
  <span className={`badge ${className}`}>{text}</span>
);

// ── Spinner ──────────────────────────────────────────────────────────────────
export const Spinner: React.FC<{ size?: number }> = ({ size = 20 }) => (
  <div className="spinner" style={{ width: size, height: size }} />
);

// ── Empty State ──────────────────────────────────────────────────────────────
export const EmptyState: React.FC<{ icon?: string; text: string }> = ({ icon = '📭', text }) => (
  <div className="empty-state">
    <div className="empty-state-icon">{icon}</div>
    <div className="empty-state-text">{text}</div>
  </div>
);

// ── Info Row ─────────────────────────────────────────────────────────────────
export const InfoRow: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div className="info-row">
    <span className="info-key">{label}</span>
    <span className="info-val">{value}</span>
  </div>
);

// ── Simulation Badge ─────────────────────────────────────────────────────────
export const SimBadge: React.FC = () => (
  <span className="sim-badge">⚡ Simulation Mode</span>
);
