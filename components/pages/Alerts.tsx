'use client';

import { useSimulation } from '@/lib/store';
import { useEffect, useState } from 'react';
import { Alert, AlertSeverity } from '@/lib/types';
import { Bell, CheckCheck, AlertTriangle, AlertCircle, Info, Zap, ShieldAlert } from 'lucide-react';

const SEVERITY_CONFIG = {
  critical: {
    color: 'text-cyber-danger',
    bg: 'bg-cyber-danger/5',
    border: 'border-cyber-danger/40',
    icon: <ShieldAlert size={16} className="text-cyber-danger" />,
    badge: 'bg-cyber-danger/20 text-cyber-danger border-cyber-danger/40',
  },
  high: {
    color: 'text-cyber-danger',
    bg: 'bg-cyber-danger/5',
    border: 'border-cyber-danger/20',
    icon: <AlertTriangle size={16} className="text-cyber-danger" />,
    badge: 'bg-cyber-danger/10 text-cyber-danger border-cyber-danger/30',
  },
  medium: {
    color: 'text-cyber-suspicious',
    bg: 'bg-cyber-suspicious/5',
    border: 'border-cyber-suspicious/20',
    icon: <AlertCircle size={16} className="text-cyber-suspicious" />,
    badge: 'bg-cyber-suspicious/10 text-cyber-suspicious border-cyber-suspicious/30',
  },
  low: {
    color: 'text-cyber-primary',
    bg: 'bg-cyber-primary/5',
    border: 'border-cyber-primary/20',
    icon: <Info size={16} className="text-cyber-primary" />,
    badge: 'bg-cyber-primary/10 text-cyber-primary border-cyber-primary/30',
  },
};

function formatTimestamp(d: Date) {
  const date = new Date(d);
  return date.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

export default function Alerts() {
  const { alerts, markAlertsRead, unreadAlerts } = useSimulation();
  const [filter, setFilter] = useState<AlertSeverity | 'all'>('all');
  const [showUnread, setShowUnread] = useState(false);

  useEffect(() => {
    markAlertsRead();
  }, []);

  const filtered = alerts.filter(a => {
    const matchSeverity = filter === 'all' || a.severity === filter;
    const matchUnread = !showUnread || !a.read;
    return matchSeverity && matchUnread;
  });

  const counts = {
    critical: alerts.filter(a => a.severity === 'critical').length,
    high: alerts.filter(a => a.severity === 'high').length,
    medium: alerts.filter(a => a.severity === 'medium').length,
    low: alerts.filter(a => a.severity === 'low').length,
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-lg font-bold text-cyber-primary neon-text flex items-center gap-2">
              <Bell size={18} /> Security Alerts
            </h1>
            <p className="text-xs text-cyber-muted">{alerts.length} total · {unreadAlerts} new since last visit</p>
          </div>
          <button
            onClick={markAlertsRead}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-cyber-card border border-cyber-border rounded-lg text-cyber-muted hover:text-cyber-text hover:border-cyber-border2 transition-colors"
          >
            <CheckCheck size={13} />
            Mark all read
          </button>
        </div>

        {/* Severity counters + filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 text-xs rounded font-medium border transition-colors ${
              filter === 'all'
                ? 'bg-cyber-primary/15 text-cyber-primary border-cyber-primary/40'
                : 'bg-cyber-card text-cyber-muted border-cyber-border hover:border-cyber-border2'
            }`}
          >
            All ({alerts.length})
          </button>
          {(['critical', 'high', 'medium', 'low'] as AlertSeverity[]).map(s => {
            const cfg = SEVERITY_CONFIG[s];
            return (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1.5 text-xs rounded font-medium border transition-colors ${
                  filter === s
                    ? `${cfg.badge} border`
                    : 'bg-cyber-card text-cyber-muted border-cyber-border hover:border-cyber-border2'
                }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)} ({counts[s]})
              </button>
            );
          })}
          <label className="flex items-center gap-1.5 ml-auto text-xs text-cyber-muted cursor-pointer">
            <input
              type="checkbox"
              checked={showUnread}
              onChange={e => setShowUnread(e.target.checked)}
              className="w-3.5 h-3.5"
            />
            Unread only
          </label>
        </div>
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filtered.map((alert, idx) => (
          <AlertCard key={alert.id} alert={alert} isNew={idx === 0 && !alert.read} />
        ))}
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-cyber-muted">
            <Bell size={36} className="mb-3 opacity-20" />
            <p className="text-sm">No alerts match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AlertCard({ alert, isNew }: { alert: Alert; isNew: boolean }) {
  const cfg = SEVERITY_CONFIG[alert.severity];

  return (
    <div
      className={`
        p-4 rounded-lg border fade-in-up
        ${cfg.bg} ${cfg.border}
        ${isNew ? 'ring-1 ring-cyber-danger/40' : ''}
        ${!alert.read ? 'border-l-2' : ''}
      `}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{cfg.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-sm font-bold ${cfg.color}`}>{alert.type}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase border ${cfg.badge}`}>
              {alert.severity}
            </span>
            {!alert.read && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30 font-bold">
                NEW
              </span>
            )}
          </div>
          <div className="text-xs text-cyber-dim mb-2">{alert.message}</div>
          <div className="flex items-center gap-4 text-xs text-cyber-muted">
            <span className="font-mono text-cyber-primary">{alert.deviceName}</span>
            <span>{formatTimestamp(alert.timestamp)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
