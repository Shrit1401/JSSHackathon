'use client';

import { useSimulation } from '@/lib/store';
import { useEffect, useState, useRef } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
  Wifi,
  AlertCircle,
  UserPlus,
  TrendingDown,
  Zap,
  Lock,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { NetworkEvent } from '@/lib/types';

const EVENT_ICONS: Record<string, React.ReactNode> = {
  device_joined: <UserPlus size={14} className="text-cyber-safe" />,
  trust_update: <TrendingDown size={14} className="text-cyber-suspicious" />,
  anomaly: <Zap size={14} className="text-cyber-danger" />,
  policy_violation: <Lock size={14} className="text-cyber-danger" />,
  new_connection: <Wifi size={14} className="text-cyber-primary" />,
  scan_detected: <AlertTriangle size={14} className="text-cyber-danger" />,
  alert_generated: <AlertCircle size={14} className="text-cyber-suspicious" />,
  device_left: <XCircle size={14} className="text-cyber-muted" />,
};

function formatTime(d: Date) {
  return new Date(d).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function Overview() {
  const { devices, alerts, events } = useSimulation();
  const [visibleFeed, setVisibleFeed] = useState<NetworkEvent[]>([]);
  const feedRef = useRef<HTMLDivElement>(null);

  const total = devices.length;
  const safe = devices.filter(d => d.riskLevel === 'safe').length;
  const suspicious = devices.filter(d => d.riskLevel === 'suspicious').length;
  const highRisk = devices.filter(d => d.riskLevel === 'high-risk').length;

  const pieData = [
    { name: 'Safe', value: safe, color: '#10b981' },
    { name: 'Suspicious', value: suspicious, color: '#f59e0b' },
    { name: 'High Risk', value: highRisk, color: '#ef4444' },
  ];

  // Traffic summary from all devices
  const trafficData = (() => {
    const len = 20;
    const result = [];
    for (let i = 0; i < len; i++) {
      let total = 0;
      devices.forEach(d => {
        const pt = d.trafficHistory[d.trafficHistory.length - len + i];
        if (pt) total += pt.value;
      });
      result.push({ time: `T-${len - i}`, value: Math.round(total) });
    }
    return result;
  })();

  // Keep recent events in feed, add new ones with animation
  useEffect(() => {
    setVisibleFeed(events.slice(0, 8));
  }, [events]);

  const recentAlerts = alerts.slice(0, 5);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-lg font-bold text-cyber-primary neon-text">Network Command Center</h1>
          <p className="text-xs text-cyber-muted">Real-time IoT security monitoring — live simulation active</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-cyber-dim">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyber-safe blink" />
            <span>Monitoring Active</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Activity size={12} className="text-cyber-primary" />
            <span>{total} devices tracked</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard
            label="Total Devices"
            value={total}
            icon={<Wifi size={20} />}
            color="text-cyber-primary"
            border="border-cyber-primary/30"
            bg="bg-cyber-primary/5"
          />
          <SummaryCard
            label="Safe Devices"
            value={safe}
            icon={<CheckCircle size={20} />}
            color="text-cyber-safe"
            border="border-cyber-safe/30"
            bg="bg-cyber-safe/5"
          />
          <SummaryCard
            label="Suspicious"
            value={suspicious}
            icon={<AlertTriangle size={20} />}
            color="text-cyber-suspicious"
            border="border-cyber-suspicious/30"
            bg="bg-cyber-suspicious/5"
            pulse="animate-pulse-yellow"
          />
          <SummaryCard
            label="High Risk"
            value={highRisk}
            icon={<XCircle size={20} />}
            color="text-cyber-danger"
            border="border-cyber-danger/30"
            bg="bg-cyber-danger/5"
            pulse="animate-pulse-red"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-5 gap-4">
          {/* Trust Distribution */}
          <div className="col-span-2 cyber-card p-4 neon-border">
            <h3 className="text-sm font-semibold text-cyber-dim mb-3 flex items-center gap-2">
              <Shield size={14} className="text-cyber-primary" />
              Trust Score Distribution
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} stroke={entry.color} strokeWidth={1} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0d1e36', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 12 }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#94a3b8' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-around text-xs">
              {pieData.map(d => (
                <div key={d.name} className="text-center">
                  <div className="font-bold text-lg" style={{ color: d.color }}>{d.value}</div>
                  <div className="text-cyber-muted">{d.name}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Network Traffic */}
          <div className="col-span-3 cyber-card p-4 neon-border">
            <h3 className="text-sm font-semibold text-cyber-dim mb-3 flex items-center gap-2">
              <Activity size={14} className="text-cyber-primary" />
              Network Traffic — All Devices (Mbps)
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trafficData}>
                <defs>
                  <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0d1e36', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 12 }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#00d4ff' }}
                />
                <Area type="monotone" dataKey="value" stroke="#00d4ff" strokeWidth={2} fill="url(#trafficGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bottom Row: Alerts + Activity Feed */}
        <div className="grid grid-cols-2 gap-4">
          {/* Recent Alerts */}
          <div className="cyber-card p-4 neon-border">
            <h3 className="text-sm font-semibold text-cyber-dim mb-3 flex items-center gap-2">
              <AlertCircle size={14} className="text-cyber-danger" />
              Recent Alerts
            </h3>
            <div className="space-y-2">
              {recentAlerts.map(alert => (
                <div
                  key={alert.id}
                  className={`flex items-start gap-3 p-2.5 rounded-lg border text-xs
                    ${alert.severity === 'critical'
                      ? 'bg-cyber-danger/5 border-cyber-danger/30'
                      : alert.severity === 'high'
                      ? 'bg-cyber-danger/5 border-cyber-danger/20'
                      : alert.severity === 'medium'
                      ? 'bg-cyber-suspicious/5 border-cyber-suspicious/20'
                      : 'bg-cyber-primary/5 border-cyber-primary/20'
                    }
                  `}
                >
                  <SeverityDot severity={alert.severity} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-cyber-text truncate">{alert.type}</div>
                    <div className="text-cyber-muted mt-0.5 line-clamp-1">{alert.deviceName}</div>
                  </div>
                  <div className="text-cyber-muted whitespace-nowrap">{formatTime(alert.timestamp)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Live Activity Feed */}
          <div className="cyber-card p-4 neon-border">
            <h3 className="text-sm font-semibold text-cyber-dim mb-3 flex items-center gap-2">
              <Activity size={14} className="text-cyber-primary" />
              Live Activity Feed
              <span className="ml-auto flex items-center gap-1 text-xs text-cyber-safe">
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-safe blink" />
                LIVE
              </span>
            </h3>
            <div ref={feedRef} className="space-y-1.5 max-h-56 overflow-y-auto">
              {visibleFeed.map((event, idx) => (
                <div
                  key={event.id}
                  className="flex items-start gap-2.5 px-2.5 py-2 rounded-lg bg-cyber-bg/60 border border-cyber-border/50 text-xs fade-in-up"
                  style={{ animationDelay: `${idx * 30}ms` }}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    {EVENT_ICONS[event.type] || <Activity size={14} className="text-cyber-muted" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-cyber-primary font-medium">{event.deviceName}</span>
                    <span className="text-cyber-dim ml-1">{event.description}</span>
                  </div>
                  <span className="text-cyber-muted whitespace-nowrap flex-shrink-0">
                    {formatTime(event.time)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
  color,
  border,
  bg,
  pulse,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  border: string;
  bg: string;
  pulse?: string;
}) {
  return (
    <div className={`cyber-card p-4 border ${border} ${bg} ${pulse || ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`${color}`}>{icon}</span>
        <span className={`text-3xl font-bold ${color}`}>{value}</span>
      </div>
      <div className="text-xs text-cyber-muted font-medium uppercase tracking-wide">{label}</div>
    </div>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-cyber-danger animate-pulse',
    high: 'bg-cyber-danger',
    medium: 'bg-cyber-suspicious',
    low: 'bg-cyber-primary',
  };
  return <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1 ${colors[severity] || 'bg-cyber-muted'}`} />;
}
