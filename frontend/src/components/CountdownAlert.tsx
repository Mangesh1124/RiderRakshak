import React, { useEffect, useRef, useState } from 'react';
import { cancelAccident, getAccident } from '../services/api';
import type { Accident } from '../types';
import { secondsUntil, severityColor } from '../utils/helpers';

interface CountdownAlertProps {
  accidentId: string;
  onResolved: (accident: Accident) => void;
}

const CountdownAlert: React.FC<CountdownAlertProps> = ({ accidentId, onResolved }) => {
  const [accident, setAccident] = useState<Accident | null>(null);
  const [seconds, setSeconds] = useState<number>(10);
  const [cancelling, setCancelling] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const pollRef = useRef<number | null>(null);

  // Poll accident status
  useEffect(() => {
    const fetch = async () => {
      try {
        const acc = await getAccident(accidentId);
        setAccident(acc);
        if (acc.status !== 'PENDING') {
          clearInterval(intervalRef.current!);
          clearInterval(pollRef.current!);
          onResolved(acc);
          return;
        }
        setSeconds(secondsUntil(acc.cancellation_deadline));
      } catch {}
    };
    fetch();
    pollRef.current = window.setInterval(fetch, 2000);
    return () => {
      clearInterval(intervalRef.current!);
      clearInterval(pollRef.current!);
    };
  }, [accidentId]);

  // Countdown tick
  useEffect(() => {
    intervalRef.current = window.setInterval(() => {
      setSeconds(s => {
        if (s <= 1) {
          clearInterval(intervalRef.current!);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current!);
  }, []);

  const handleCancel = async () => {
    setCancelling(true);
    try {
      const updated = await cancelAccident(accidentId);
      onResolved(updated);
    } catch {
      setCancelling(false);
    }
  };

  if (!accident) return null;

  return (
    <div className="countdown-wrap">
      <div style={{ fontSize: 13, color: '#fca5a5', fontWeight: 700, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
        ⚠️ Accident Detected — Alert Window
      </div>
      <div className="countdown-number">{seconds}</div>
      <div className="countdown-label">seconds until alert is automatically confirmed</div>

      <div style={{ marginTop: 16, padding: 12, background: 'rgba(0,0,0,0.3)', borderRadius: 8 }}>
        <div style={{ fontSize: 12, color: '#94a3b8' }}>Accident ID</div>
        <div style={{ fontFamily: 'JetBrains Mono', fontSize: 13, color: 'white' }}>{accident.id}</div>
        {accident.severity && (
          <div style={{ marginTop: 8 }}>
            <span style={{ color: severityColor(accident.severity), fontWeight: 700, fontSize: 13 }}>
              Severity: {accident.severity}
            </span>
          </div>
        )}
      </div>

      <div style={{ marginTop: 16, display: 'flex', gap: 10, justifyContent: 'center' }}>
        <button
          className="btn btn-danger btn-lg"
          onClick={handleCancel}
          disabled={cancelling || seconds === 0}
        >
          {cancelling ? '⏳ Cancelling…' : '✋ FALSE ALERT — Cancel'}
        </button>
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
        If you do not cancel, the alert will be confirmed automatically.
      </div>
    </div>
  );
};

export default CountdownAlert;
