'use client';

import { useSimulation } from '@/lib/store';
import { NetworkEvent, EventType } from '@/lib/types';
import { Clock, Wifi, TrendingDown, Zap, Lock, Network, ScanLine, AlertCircle, UserPlus, LogOut } from 'lucide-react';

const EVENT_CONFIG: Record<EventType, {
  icon: React.ReactNode;
  color: string;
  bg: string;
  border: string;
  label: string;
}> = {
  device_joined: {
    icon: <UserPlus size={14} />,
    color: 'text-cyber-safe',
    bg: 'bg-cyber-safe/10',
    border: 'border-cyber-safe/30',
    label: 'Device Joined',
  },
  device_left: {
    icon: <LogOut size={14} />,
    color: 'text-cyber-muted',
    bg: 'bg-cyber-card',
    border: 'border-cyber-border',
    label: 'Device Left',
  },
  traffic_spike: {
    icon: <Zap size={14} />,
    color: 'text-cyber-suspicious',
    bg: 'bg-cyber-suspicious/10',
    border: 'border-cyber-suspicious/30',
    label: 'Traffic Spike',
  },
  trust_update: {
    icon: <TrendingDown size={14} />,
    color: 'text-cyber-suspicious',
    bg: 'bg-cyber-suspicious/5',
    border: 'border-cyber-suspicious/20',
    label: 'Trust Updated',
  },
  anomaly: {
    icon: <Zap size={14} />,
    color: 'text-cyber-danger',
    bg: 'bg-cyber-danger/10',
    border: 'border-cyber-danger/30',
    label: 'Anomaly',
  },
  policy_violation: {
    icon: <Lock size={14} />,
    color: 'text-cyber-danger',
    bg: 'bg-cyber-danger/5',
    border: 'border-cyber-danger/20',
    label: 'Policy Violation',
  },
  new_connection: {
    icon: <Network size={14} />,
    color: 'text-cyber-primary',
    bg: 'bg-cyber-primary/5',
    border: 'border-cyber-primary/20',
    label: 'New Connection',
  },
  scan_detected: {
    icon: <ScanLine size={14} />,
    color: 'text-cyber-danger',
    bg: 'bg-cyber-danger/10',
    border: 'border-cyber-danger/40',
    label: 'Port Scan',
  },
  alert_generated: {
    icon: <AlertCircle size={14} />,
    color: 'text-cyber-suspicious',
    bg: 'bg-cyber-suspicious/5',
    border: 'border-cyber-suspicious/20',
    label: 'Alert',
  },
};

function formatRelative(d: Date) {
  const now = new Date();
  const diff = Math.floor((now.getTime() - new Date(d).getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function formatTime(d: Date) {
  return new Date(d).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

function groupByMinute(events: NetworkEvent[]) {
  const groups: Map<string, NetworkEvent[]> = new Map();
  events.forEach(evt => {
    const key = new Date(evt.time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(evt);
  });
  return Array.from(groups.entries());
}

export default function EventsTimeline() {
  const { events } = useSimulation();
  const groups = groupByMinute(events);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-cyber-primary neon-text flex items-center gap-2">
              <Clock size={18} /> Events Timeline
            </h1>
            <p className="text-xs text-cyber-muted">{events.length} events recorded · auto-updating</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-cyber-safe">
            <span className="w-2 h-2 rounded-full bg-cyber-safe blink" />
            <span>Live</span>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-[116px] top-0 bottom-0 w-px bg-cyber-border" />

          {groups.map(([timeKey, groupEvents], groupIdx) => (
            <div key={timeKey} className="mb-6">
              {/* Time marker */}
              <div className="flex items-center mb-3">
                <div className="w-[100px] text-xs text-cyber-muted text-right pr-4 font-mono">{timeKey}</div>
                <div className="relative z-10 w-4 h-4 rounded-full bg-cyber-primary border-2 border-cyber-bg flex-shrink-0 mx-3" />
                <div className="text-xs text-cyber-muted">{groupEvents.length} event{groupEvents.length > 1 ? 's' : ''}</div>
              </div>

              {/* Events in this time group */}
              <div className="ml-[132px] space-y-2">
                {groupEvents.map((evt, i) => {
                  const cfg = EVENT_CONFIG[evt.type] || EVENT_CONFIG['alert_generated'];
                  return (
                    <div
                      key={evt.id}
                      className={`
                        relative flex items-start gap-3 p-3 rounded-lg border text-xs fade-in-up
                        ${cfg.bg} ${cfg.border}
                      `}
                      style={{ animationDelay: `${i * 40}ms` }}
                    >
                      {/* Connector dot */}
                      <div className="absolute -left-[22px] top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-cyber-border border-2 border-cyber-surface" />

                      <div className={`flex-shrink-0 mt-0.5 ${cfg.color}`}>{cfg.icon}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className={`font-bold ${cfg.color}`}>{cfg.label}</span>
                          <span className="text-cyber-primary font-mono">{evt.deviceName}</span>
                        </div>
                        <div className="text-cyber-dim leading-relaxed">{evt.description}</div>
                      </div>
                      <div className="text-cyber-muted whitespace-nowrap flex-shrink-0 font-mono">
                        {formatTime(evt.time)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {events.length === 0 && (
            <div className="flex flex-col items-center justify-center h-48 text-cyber-muted">
              <Clock size={36} className="mb-3 opacity-20" />
              <p className="text-sm">No events recorded yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
