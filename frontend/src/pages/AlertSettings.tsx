import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';

const API: string = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

type EmailInfo = {
  recipients: string[];
  email_enabled: boolean;
  sender: string;
  alcohol_alert_index: number;
  cooldown_seconds: number;
};
type Msg = { ok: boolean; text: string } | null;

const s: Record<string, CSSProperties> = {
  card: { background: 'var(--bg-card, #111c33)', border: '1px solid var(--border, #1f2d4d)', borderRadius: 12, padding: 24, maxWidth: 640 },
  h2: { margin: '0 0 4px', fontSize: 22 },
  sub: { color: 'var(--text-secondary, #8a97b5)', margin: '0 0 20px', fontSize: 14 },
  row: { display: 'flex', gap: 8, marginBottom: 12 },
  input: { flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #2a3b61', background: '#0b1426', color: '#e6ecff' },
  btn: { padding: '10px 16px', borderRadius: 8, border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer' },
  btn2: { padding: '10px 16px', borderRadius: 8, border: '1px solid #2a3b61', background: 'transparent', color: '#e6ecff', cursor: 'pointer' },
  chip: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', marginBottom: 8, borderRadius: 8, background: '#0b1426', border: '1px solid #1f2d4d' },
  x: { background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 16 },
  meta: { color: 'var(--text-secondary, #8a97b5)', fontSize: 13, marginTop: 16, lineHeight: 1.6 },
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? 'Invalid request' : data.detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return data as T;
}

const AlertSettings = () => {
  const [recipients, setRecipients] = useState<string[]>([]);
  const [info, setInfo] = useState<EmailInfo | null>(null);
  const [input, setInput] = useState('');
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);

  useEffect(() => {
    api<EmailInfo>('/api/notifications/email')
      .then((d) => { setInfo(d); setRecipients(d.recipients); })
      .catch((e: Error) => setMsg({ ok: false, text: e.message }));
  }, []);

  const add = () => {
    const email = input.trim().toLowerCase();
    if (!email) return;
    if (!EMAIL_RE.test(email)) return setMsg({ ok: false, text: 'That is not a valid email address' });
    if (recipients.includes(email)) return setMsg({ ok: false, text: 'Already in the list' });
    setRecipients([...recipients, email]);
    setInput('');
    setDirty(true);
    setMsg(null);
  };

  const remove = (email: string) => {
    setRecipients(recipients.filter((e) => e !== email));
    setDirty(true);
    setMsg(null);
  };

  const save = async () => {
    setBusy(true);
    try {
      const d = await api<{ recipients: string[] }>('/api/notifications/email', {
        method: 'PUT',
        body: JSON.stringify({ recipients }),
      });
      setRecipients(d.recipients);
      setDirty(false);
      setMsg({ ok: true, text: 'Saved. Alerts will go to these addresses.' });
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    }
    setBusy(false);
  };

  const sendTest = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const d = await api<{ sent_to: string[] }>('/api/notifications/email/test', { method: 'POST' });
      setMsg({ ok: true, text: `Test email sent to ${d.sent_to.join(', ')}. Check the inbox and spam.` });
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    }
    setBusy(false);
  };

  return (
    <div style={s.card}>
      <h2 style={s.h2}>Alert receivers</h2>
      <p style={s.sub}>These addresses get an encrypted email when alcohol or an accident is detected.</p>

      <div style={s.row}>
        <input
          style={s.input}
          type="email"
          placeholder="name@example.com"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
        />
        <button style={s.btn2} onClick={add}>Add</button>
      </div>

      {recipients.length === 0 && <p style={s.sub}>No receivers yet. No emails will be sent.</p>}
      {recipients.map((email) => (
        <div key={email} style={s.chip}>
          <span>{email}</span>
          <button style={s.x} onClick={() => remove(email)} title="Remove">✕</button>
        </div>
      ))}

      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <button style={{ ...s.btn, opacity: dirty ? 1 : 0.5 }} disabled={!dirty || busy} onClick={save}>
          {busy ? 'Working...' : 'Save receivers'}
        </button>
        <button
          style={s.btn2}
          disabled={dirty || busy || recipients.length === 0}
          onClick={sendTest}
          title={dirty ? 'Save first' : ''}
        >
          Send test email
        </button>
      </div>

      {msg && <p style={{ color: msg.ok ? '#34d399' : '#f87171', marginTop: 16 }}>{msg.text}</p>}

      {info && (
        <div style={s.meta}>
          Sender: {info.sender || 'not set'}<br />
          Email alerts: {info.email_enabled ? 'ON' : 'OFF (set EMAIL_ENABLED=true on the server)'}<br />
          Sent when the alcohol index reaches {info.alcohol_alert_index}, at most once every {info.cooldown_seconds} seconds.
          Alcohol emails go out when the index reaches {info.alcohol_alert_index}, at most once every {info.cooldown_seconds} seconds. Each email carries the last 10 seconds of readings.
        </div>
      )}
    </div>
  );
};

export default AlertSettings;