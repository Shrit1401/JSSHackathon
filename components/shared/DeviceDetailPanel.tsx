'use client';

import { Device } from '@/lib/types';
import { X, Cpu, Globe, Network, AlertTriangle, Server } from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import StatusBadge from './StatusBadge';

interface Props {
  device: Device;
  onClose: () => void;
}

const DEVICE_ICONS: Record<string, string> = {
  Laptop: '💻',
  Phone: '📱',
  Printer: '🖨️',
  'Smart TV': '📺',
  'Security Camera': '📷',
  Router: '📡',
  'IoT Sensor': '🔌',
  Server: '🖥️',
  Tablet: '📲',
};

export default function DeviceDetailPanel({ device, onClose }: Props) {
  const trustColor =
    device.riskLevel === 'safe'
      ? '#10b981'
      : device.riskLevel === 'suspicious'
      ? '#f59e0b'
      : '#ef4444';

  const trustData = device.trustHistory.slice(-20);
  const trafficData = device.trafficHistory.slice(-20);

  return (
    <div className="h-full flex flex-col bg-cyber-surface border-l border-cyber-border slide-in-right overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-cyber-border flex items-start justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyber-card flex items-center justify-center text-xl border border-cyber-border">
            {DEVICE_ICONS[device.type] || '📟'}
          </div>
          <div>
            <div className="font-bold text-cyber-text">{device.name}</div>
            <div className="text-xs text-cyber-muted">{device.type} · {device.vendor}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge level={device.riskLevel} />
          <button
            onClick={onClose}
            className="text-cyber-muted hover:text-cyber-text p-1 rounded hover:bg-cyber-card transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Trust Score */}
        <div className="cyber-card p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-cyber-dim uppercase tracking-wider">Trust Score</span>
            <span className="text-2xl font-bold" style={{ color: trustColor }}>
              {Math.round(device.trustScore)}
            </span>
          </div>
          <div className="w-full bg-cyber-bg rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-500"
              style={{ width: `${device.trustScore}%`, backgroundColor: trustColor }}
            />
          </div>
        </div>

        {/* Device Info */}
        <div className="cyber-card p-3">
          <div className="text-xs font-semibold text-cyber-dim uppercase tracking-wider mb-3 flex items-center gap-2">
            <Server size={12} /> Device Information
          </div>
          <div className="space-y-2 text-xs">
            <InfoRow label="IP Address" value={device.ip} />
            <InfoRow label="MAC Address" value={device.mac} />
            <InfoRow label="Vendor" value={device.vendor} />
            <InfoRow label="OS" value={device.os || 'Unknown'} />
            <InfoRow label="Location" value={device.location || 'Unknown'} />
            <InfoRow label="Traffic Rate" value={`${device.trafficRate.toFixed(1)} Mbps`} />
            <div className="flex items-center justify-between">
              <span className="text-cyber-muted">Open Ports</span>
              <div className="flex gap-1 flex-wrap justify-end">
                {device.ports.map(port => (
                  <span key={port} className="px-1.5 py-0.5 bg-cyber-bg border border-cyber-border rounded text-cyber-primary font-mono">
                    {port}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Trust Score History */}
        <div className="cyber-card p-3">
          <div className="text-xs font-semibold text-cyber-dim uppercase tracking-wider mb-3 flex items-center gap-2">
            <Network size={12} /> Trust Score History
          </div>
          <ResponsiveContainer width="100%" height={100}>
            <LineChart data={trustData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{ background: '#0d1e36', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
                itemStyle={{ color: trustColor }}
              />
              <Line type="monotone" dataKey="value" stroke={trustColor} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Traffic History */}
        <div className="cyber-card p-3">
          <div className="text-xs font-semibold text-cyber-dim uppercase tracking-wider mb-3 flex items-center gap-2">
            <Globe size={12} /> Traffic Rate (Mbps)
          </div>
          <ResponsiveContainer width="100%" height={90}>
            <AreaChart data={trafficData}>
              <defs>
                <linearGradient id={`tg-${device.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" hide />
              <YAxis hide />
              <Tooltip
                contentStyle={{ background: '#0d1e36', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
                itemStyle={{ color: '#00d4ff' }}
              />
              <Area type="monotone" dataKey="value" stroke="#00d4ff" strokeWidth={1.5} fill={`url(#tg-${device.id})`} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Protocol Usage */}
        <div className="cyber-card p-3">
          <div className="text-xs font-semibold text-cyber-dim uppercase tracking-wider mb-3 flex items-center gap-2">
            <Cpu size={12} /> Protocol Usage
          </div>
          <ResponsiveContainer width="100%" height={90}>
            <BarChart data={device.protocolUsage} layout="vertical">
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis type="category" dataKey="protocol" tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} axisLine={false} width={65} />
              <Tooltip
                contentStyle={{ background: '#0d1e36', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
                itemStyle={{ color: '#00d4ff' }}
                formatter={(v: number) => [`${v}%`, 'Usage']}
              />
              <Bar dataKey="percentage" radius={[0, 3, 3, 0]}>
                {device.protocolUsage.map((_, i) => (
                  <Cell key={i} fill={`hsl(${190 + i * 25}, 80%, 55%)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Security Explanation */}
        {device.flagReason && (
          <div className="cyber-card p-3 border border-cyber-danger/30 bg-cyber-danger/5">
            <div className="text-xs font-semibold text-cyber-danger uppercase tracking-wider mb-2 flex items-center gap-2">
              <AlertTriangle size={12} /> Security Analysis
            </div>
            <p className="text-xs text-cyber-dim leading-relaxed">{device.flagReason}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-cyber-muted flex-shrink-0">{label}</span>
      <span className="text-cyber-text font-mono text-right truncate">{value}</span>
    </div>
  );
}
