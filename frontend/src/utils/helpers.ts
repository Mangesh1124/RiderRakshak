// Utility helpers
import type { Accident, Severity } from '../types';

export function formatTs(ts: string | null | undefined): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  });
}

export function formatNum(n: number | null | undefined, decimals = 2): string {
  if (n == null) return '—';
  return n.toFixed(decimals);
}

export function classificationBadgeClass(c: string): string {
  const m: Record<string, string> = {
    NORMAL: 'badge-normal',
    SUSPICIOUS: 'badge-suspicious',
    POSSIBLE_ACCIDENT: 'badge-possible',
    CONFIRMED_ACCIDENT: 'badge-confirmed',
  };
  return m[c] ?? 'badge-normal';
}

export function statusBadgeClass(s: string): string {
  const m: Record<string, string> = {
    PENDING: 'badge-pending',
    CONFIRMED_ACCIDENT: 'badge-confirmed',
    FALSE_ALERT_CANCELLED: 'badge-cancelled',
  };
  return m[s] ?? 'badge-normal';
}

export function severityBadgeClass(s: string | null): string {
  const m: Record<string, string> = {
    LOW: 'badge-low',
    MEDIUM: 'badge-medium',
    HIGH: 'badge-high',
    CRITICAL: 'badge-critical',
  };
  return m[s ?? ''] ?? 'badge-normal';
}

export function scoreColor(score: number): string {
  if (score < 0.25) return '#10b981';
  if (score < 0.45) return '#f59e0b';
  if (score < 0.70) return '#f97316';
  return '#ef4444';
}

export function severityColor(s: string | null): string {
  const m: Record<string, string> = {
    LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444',
  };
  return m[s ?? ''] ?? '#94a3b8';
}

export function secondsUntil(deadline: string | null): number {
  if (!deadline) return 0;
  const diff = new Date(deadline + 'Z').getTime() - Date.now();
  return Math.max(0, Math.floor(diff / 1000));
}
