import React, { useEffect, useState, useCallback } from 'react';
import { getAccidents } from '../services/api';
import type { AccidentListResponse } from '../types';
import { Badge, Spinner, EmptyState } from '../components/UI';
import { formatTs, formatNum, statusBadgeClass, severityBadgeClass, classificationBadgeClass, scoreColor } from '../utils/helpers';

interface AccidentEventsProps {
  onSelectAccident?: (id: string) => void;
}

const AccidentEvents: React.FC<AccidentEventsProps> = ({ onSelectAccident }) => {
  const [data, setData] = useState<AccidentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');

  const fetchData = useCallback(async () => {
    const res = await getAccidents(100);
    setData(res);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
    const t = setInterval(fetchData, 5000);
    return () => clearInterval(t);
  }, [fetchData]);

  const statuses = ['ALL', 'PENDING', 'CONFIRMED_ACCIDENT', 'FALSE_ALERT_CANCELLED'];
  const filtered = (data?.accidents ?? []).filter(a => filter === 'ALL' || a.status === filter);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spinner size={32} /></div>;

  return (
    <div className="page-gap">
      {/* Stats row */}
      <div className="grid-4">
        {['ALL', 'PENDING', 'CONFIRMED_ACCIDENT', 'FALSE_ALERT_CANCELLED'].map(s => {
          const count = s === 'ALL'
            ? (data?.total ?? 0)
            : (data?.accidents ?? []).filter(a => a.status === s).length;
          const colors: Record<string, string> = { ALL: 'blue', PENDING: 'yellow', CONFIRMED_ACCIDENT: 'red', FALSE_ALERT_CANCELLED: 'green' };
          return (
            <div key={s} className={`metric-card accent-${colors[s]}`} style={{ cursor: 'pointer', opacity: filter === s ? 1 : 0.7 }} onClick={() => setFilter(s)}>
              <div className="metric-label">{s.replace(/_/g, ' ')}</div>
              <div className="metric-value">{count}</div>
            </div>
          );
        })}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">🚨 Accident Events</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {statuses.map(s => (
              <button key={s} className={`btn btn-sm ${filter === s ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilter(s)}>
                {s === 'ALL' ? 'All' : s.split('_').slice(-1)[0]}
              </button>
            ))}
          </div>
        </div>
        {filtered.length === 0 ? (
          <EmptyState icon="🔍" text={`No ${filter === 'ALL' ? '' : filter.replace(/_/g, ' ').toLowerCase() + ' '}accidents recorded`} />
        ) : (
          <div className="table-wrap" style={{ borderRadius: 0, border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Time</th>
                  <th>Classification</th>
                  <th>Score</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>GPS</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(acc => (
                  <tr key={acc.id}>
                    <td className="mono">{acc.id}</td>
                    <td>{formatTs(acc.timestamp)}</td>
                    <td><Badge text={acc.classification.replace(/_/g, ' ')} className={classificationBadgeClass(acc.classification)} /></td>
                    <td>
                      <span style={{ fontFamily: 'JetBrains Mono', fontWeight: 700, color: scoreColor(acc.accident_score) }}>
                        {formatNum(acc.accident_score, 3)}
                      </span>
                    </td>
                    <td>{acc.severity ? <Badge text={acc.severity} className={severityBadgeClass(acc.severity)} /> : '—'}</td>
                    <td><Badge text={acc.status.replace(/_/g, ' ')} className={statusBadgeClass(acc.status)} /></td>
                    <td className="mono" style={{ fontSize: 11 }}>
                      {acc.latitude ? `${formatNum(acc.latitude, 4)}, ${formatNum(acc.longitude, 4)}` : '—'}
                    </td>
                    <td>
                      <button className="btn btn-sm btn-ghost" onClick={() => onSelectAccident?.(acc.id)}>
                        View →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AccidentEvents;
