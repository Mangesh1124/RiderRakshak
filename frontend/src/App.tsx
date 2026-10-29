import React, { useState, useEffect } from 'react';
import './index.css';
import Dashboard from './pages/Dashboard';
import LiveSensors from './pages/LiveSensors';
import AccidentEvents from './pages/AccidentEvents';
import AccidentDetails from './pages/AccidentDetails';
import SimulationControl from './pages/SimulationControl';
import AlertSettings from './pages/AlertSettings';
import EvidenceViewer from './pages/EvidenceViewer';
import SystemInfo from './pages/SystemInfo';
import { getSystemStatus } from './services/api';

type Page =
  | 'dashboard'
  | 'live'
  | 'accidents'
  | 'accident-detail'
  | 'simulation'
  | 'alert-settings'
  | 'evidence'
  | 'system';

interface NavItem {
  id: Page;
  label: string;
  icon: string;
}

const NAV: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
  { id: 'live', label: 'Live Sensors', icon: '📡' },
  { id: 'simulation', label: 'Simulation Control', icon: '🎮' },
  { id: 'accidents', label: 'Accident Events', icon: '🚨' },
  { id: 'alert-settings', label: 'Alert Receivers', icon: '📧' },
  { id: 'evidence', label: 'Decrypt Alerts', icon: '🔓' },
  { id: 'system', label: 'System Info', icon: '⚙️' },
];

const PAGE_TITLES: Record<Page, { title: string; subtitle: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'System overview and recent events' },
  live: { title: 'Live Sensors', subtitle: 'Real-time sensor data [SIMULATION MODE]' },
  simulation: { title: 'Simulation Control', subtitle: 'Trigger scenarios and test the pipeline' },
  accidents: { title: 'Accident Events', subtitle: 'Complete accident history and management' },
  'accident-detail': { title: 'Accident Details', subtitle: 'Full accident record with GSM alert' },
  'alert-settings': { title: 'Alert Receivers', subtitle: 'Who gets the alert emails' },
  evidence: { title: 'Decrypt Alerts', subtitle: 'Verify integrity and read encrypted alert files' },
  system: { title: 'System Information', subtitle: 'Architecture, hardware status, and configuration' },
};

const App: React.FC = () => {
  const [page, setPage] = useState<Page>('dashboard');
  const [selectedAccidentId, setSelectedAccidentId] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  // Check backend health
  useEffect(() => {
    getSystemStatus()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false));
  }, []);

  const navigate = (p: Page) => {
    setPage(p);
    if (p !== 'accident-detail') setSelectedAccidentId(null);
  };

  const openAccident = (id: string) => {
    setSelectedAccidentId(id);
    setPage('accident-detail');
  };

  const { title, subtitle } = PAGE_TITLES[page];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>RideRakshak</h1>
          <p>Smart Helmet MVP</p>
          <div className="sim-badge">⚡ Simulation Mode</div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {NAV.map(item => (
            <button
              key={item.id}
              className={`nav-link ${page === item.id || (item.id === 'accidents' && page === 'accident-detail') ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}

          <div className="nav-section-label" style={{ marginTop: 32 }}>System</div>
          <div style={{ padding: '8px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, marginBottom: 6 }}>
              <div className={`dot ${backendOk === true ? 'green' : backendOk === false ? 'red' : 'gray'}`} />
              <span style={{ color: 'var(--text-secondary)' }}>
                Backend: {backendOk === true ? 'Online' : backendOk === false ? 'Offline' : 'Checking…'}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              API: localhost:8000<br />
              DB: SQLite
            </div>
          </div>

          <div style={{ padding: '16px 12px', borderTop: '1px solid var(--border-subtle)', marginTop: 24 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.8 }}>
              RideRakshak v1.0.0-mvp<br />
              SOFTWARE PROTOTYPE<br />
              Hardware integration pending<br />
              © 2026 Academic Project
            </div>
          </div>
        </nav>
      </aside>

      {/* Main */}
      <div className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <div>
            <div className="page-title">{title}</div>
            <div className="page-subtitle">{subtitle}</div>
          </div>
          <div className="header-status">
            {backendOk === false && (
              <div className="alert-box danger" style={{ padding: '6px 12px', marginBottom: 0, fontSize: 12 }}>
                ⚠️ Backend offline — start: <code>uvicorn app.main:app --reload</code>
              </div>
            )}
            <div className="status-dot">
              <div className={`dot ${backendOk === true ? 'green' : 'red'}`} />
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {backendOk === true ? 'Backend Online' : 'Backend Offline'}
              </span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">
          {page === 'dashboard' && <Dashboard />}
          {page === 'live' && <LiveSensors />}
          {page === 'simulation' && <SimulationControl />}
          {page === 'accidents' && <AccidentEvents onSelectAccident={openAccident} />}
          {page === 'accident-detail' && selectedAccidentId && (
            <AccidentDetails
              accidentId={selectedAccidentId}
              onBack={() => navigate('accidents')}
            />
          )}
          {page === 'alert-settings' && <AlertSettings />}
          {page === 'evidence' && <EvidenceViewer />}
          {page === 'system' && <SystemInfo />}
        </div>
      </div>
    </div>
  );
};

export default App;