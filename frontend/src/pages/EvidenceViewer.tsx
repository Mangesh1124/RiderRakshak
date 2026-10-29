import { useState } from 'react';
import type { ChangeEvent, CSSProperties } from 'react';

const API: string = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type PublicInfo = {
  gps_fix?: boolean;
  latitude?: number;
  longitude?: number;
  maps_link?: string;
};

type History = {
  window_seconds: number;
  samples: number;
  columns: string[];
  rows: (string | number | null)[][];
};

type Result = {
  valid: boolean;
  detail?: string;
  rider_id?: string;
  encrypted_at?: string;
  public?: PublicInfo | null;
  record?: Record<string, any>;
};

const s: Record<string, CSSProperties> = {
  card: { background: 'var(--bg-card, #111c33)', border: '1px solid var(--border, #1f2d4d)', borderRadius: 12, padding: 24, marginBottom: 16 },
  h2: { margin: '0 0 4px', fontSize: 20 },
  sub: { color: 'var(--text-secondary, #8a97b5)', margin: '0 0 16px', fontSize: 14 },
  input: { padding: '10px 12px', borderRadius: 8, border: '1px solid #2a3b61', background: '#0b1426', color: '#e6ecff', width: '100%', boxSizing: 'border-box' },
  btn: { padding: '10px 16px', borderRadius: 8, border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer' },
  btn2: { padding: '8px 14px', borderRadius: 8, border: '1px solid #2a3b61', background: 'transparent', color: '#e6ecff', cursor: 'pointer' },
  label: { display: 'block', fontSize: 13, color: '#8a97b5', margin: '12px 0 6px' },
  pre: { background: '#0b1426', border: '1px solid #1f2d4d', borderRadius: 8, padding: 12, fontSize: 12, overflow: 'auto', maxHeight: 320 },
  tableWrap: { overflow: 'auto', maxHeight: 340, border: '1px solid #1f2d4d', borderRadius: 8 },
  th: { position: 'sticky', top: 0, background: '#0b1426', padding: '6px 10px', textAlign: 'left', fontSize: 12, whiteSpace: 'nowrap' },
  td: { padding: '5px 10px', fontSize: 12, whiteSpace: 'nowrap', borderTop: '1px solid #1a2745' },
};

const EvidenceViewer = () => {
  const [token, setToken] = useState('');
  const [fileName, setFileName] = useState('');
  const [envelope, setEnvelope] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setResult(null);
    setError(null);
    setEnvelope(null);
    if (!f) return;
    setFileName(f.name);
    try {
      const data = JSON.parse(await f.text());
      for (const k of ['v', 'alg', 'rider_id', 'ts', 'iv', 'ct', 'hmac']) {
        if (!(k in data)) throw new Error(`missing field "${k}"`);
      }
      setEnvelope(data);
    } catch (err) {
      setError(`Not a valid RideRakshak alert file: ${(err as Error).message}`);
    }
  };

  const decrypt = async () => {
    if (!envelope) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/api/evidence/decrypt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
        body: JSON.stringify(envelope),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${res.status})`);
      }
      setResult(data as Result);
    } catch (err) {
      setError((err as Error).message);
    }
    setBusy(false);
  };

  const record = result?.valid ? result.record : undefined;
  const history = record?.history as History | undefined;
  const pub = result?.public;
  const rest = record
    ? Object.fromEntries(Object.entries(record).filter(([k]) => k !== 'history'))
    : undefined;

  const downloadCsv = () => {
    if (!history) return;
    const lines = [
      history.columns.join(','),
      ...history.rows.map((r) => r.map((v) => (v ?? '')).join(',')),
    ];
    const url = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `history_${result?.rider_id ?? 'rider'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={s.card}>
        <h2 style={s.h2}>Decrypt an alert</h2>
        <p style={s.sub}>
          Upload the .json file attached to an alert email. The server checks its HMAC-SHA256 tag first and decrypts it only if it has not been modified.
        </p>

        <label style={s.label}>Alert file</label>
        <input type="file" accept=".json,application/json" onChange={onFile} style={{ color: '#e6ecff' }} />
        {fileName && <div style={{ fontSize: 12, color: '#8a97b5', marginTop: 6 }}>{fileName}</div>}

        <label style={s.label}>Access code</label>
        <input
          style={s.input}
          type="password"
          autoComplete="off"
          placeholder="Access code set by the administrator"
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />

        <div style={{ marginTop: 16 }}>
          <button
            style={{ ...s.btn, opacity: envelope && token ? 1 : 0.5 }}
            disabled={!envelope || !token || busy}
            onClick={decrypt}
          >
            {busy ? 'Checking...' : 'Verify and decrypt'}
          </button>
        </div>

        {error && <p style={{ color: '#f87171', marginTop: 16 }}>{error}</p>}
      </div>

      {result && !result.valid && (
        <div style={{ ...s.card, borderColor: '#7f1d1d' }}>
          <h2 style={{ ...s.h2, color: '#f87171' }}>INVALID: not decrypted</h2>
          <p style={s.sub}>{result.detail}</p>
          <p style={s.sub}>The file was modified after it was created, or it was encrypted with a different key.</p>
        </div>
      )}

      {result?.valid && record && (
        <>
          <div style={{ ...s.card, borderColor: '#065f46' }}>
            <h2 style={{ ...s.h2, color: '#34d399' }}>VALID: record has not been modified</h2>
            <p style={s.sub}>
              Rider {result.rider_id} · encrypted at (UTC) {result.encrypted_at} · event {String(record.event)}
            </p>
            <div style={{ fontSize: 14, lineHeight: 1.8 }}>
              Verified location:{' '}
              {pub?.gps_fix && pub.maps_link ? (
                <a href={pub.maps_link} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
                  {pub.latitude}, {pub.longitude} (open in Google Maps)
                </a>
              ) : (
                'GPS fix was not available'
              )}
            </div>
          </div>

          <div style={s.card}>
            <h2 style={s.h2}>Record details</h2>
            <pre style={s.pre}>{JSON.stringify(rest, null, 2)}</pre>
          </div>

          {history && (
            <div style={s.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={s.h2}>Previous {history.window_seconds} seconds</h2>
                  <p style={s.sub}>{history.samples} readings</p>
                </div>
                <button style={s.btn2} onClick={downloadCsv}>Download CSV</button>
              </div>
              <div style={s.tableWrap}>
                <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                  <thead>
                    <tr>{history.columns.map((c) => <th key={c} style={s.th}>{c}</th>)}</tr>
                  </thead>
                  <tbody>
                    {history.rows.map((r, i) => (
                      <tr key={i}>{r.map((v, j) => <td key={j} style={s.td}>{v ?? ''}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EvidenceViewer;