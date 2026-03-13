'use client';

import { useState, useMemo } from 'react';
import { useSimulation } from '@/lib/store';
import { Device, RiskLevel } from '@/lib/types';
import StatusBadge from '@/components/shared/StatusBadge';
import DeviceDetailPanel from '@/components/shared/DeviceDetailPanel';
import { Search, Filter, Monitor, Wifi, SortAsc } from 'lucide-react';

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

function formatLastSeen(d: Date) {
  const now = new Date();
  const diff = Math.floor((now.getTime() - new Date(d).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function Devices() {
  const { devices } = useSimulation();
  const [selected, setSelected] = useState<Device | null>(null);
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState<RiskLevel | 'all'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'trust' | 'traffic'>('trust');

  const filtered = useMemo(() => {
    return devices
      .filter(d => {
        const matchSearch =
          d.name.toLowerCase().includes(search.toLowerCase()) ||
          d.ip.includes(search) ||
          d.vendor.toLowerCase().includes(search.toLowerCase());
        const matchRisk = filterRisk === 'all' || d.riskLevel === filterRisk;
        return matchSearch && matchRisk;
      })
      .sort((a, b) => {
        if (sortBy === 'trust') return a.trustScore - b.trustScore;
        if (sortBy === 'traffic') return b.trafficRate - a.trafficRate;
        return a.name.localeCompare(b.name);
      });
  }, [devices, search, filterRisk, sortBy]);

  return (
    <div className="h-full flex overflow-hidden">
      {/* Device List */}
      <div className={`flex flex-col overflow-hidden transition-all duration-300 ${selected ? 'w-[60%]' : 'w-full'}`}>
        {/* Toolbar */}
        <div className="px-5 py-3 border-b border-cyber-border bg-cyber-surface/60 flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-lg font-bold text-cyber-primary neon-text">Device Inventory</h1>
              <p className="text-xs text-cyber-muted">{filtered.length} of {devices.length} devices shown</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-xs">
                <span className="w-2 h-2 rounded-full bg-cyber-safe" />
                <span className="text-cyber-muted">{devices.filter(d => d.riskLevel === 'safe').length} safe</span>
              </div>
              <div className="flex items-center gap-1 text-xs">
                <span className="w-2 h-2 rounded-full bg-cyber-suspicious" />
                <span className="text-cyber-muted">{devices.filter(d => d.riskLevel === 'suspicious').length} suspicious</span>
              </div>
              <div className="flex items-center gap-1 text-xs">
                <span className="w-2 h-2 rounded-full bg-cyber-danger" />
                <span className="text-cyber-muted">{devices.filter(d => d.riskLevel === 'high-risk').length} high risk</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-cyber-muted" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by name, IP, or vendor..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-cyber-card border border-cyber-border rounded-lg text-cyber-text placeholder:text-cyber-muted focus:outline-none focus:border-cyber-primary/50"
              />
            </div>

            {/* Risk filter */}
            <div className="flex items-center gap-1">
              <Filter size={13} className="text-cyber-muted" />
              {(['all', 'safe', 'suspicious', 'high-risk'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setFilterRisk(f)}
                  className={`px-2.5 py-1.5 text-xs rounded font-medium transition-colors ${
                    filterRisk === f
                      ? f === 'all' ? 'bg-cyber-primary/20 text-cyber-primary border border-cyber-primary/40'
                        : f === 'safe' ? 'bg-cyber-safe/20 text-cyber-safe border border-cyber-safe/40'
                        : f === 'suspicious' ? 'bg-cyber-suspicious/20 text-cyber-suspicious border border-cyber-suspicious/40'
                        : 'bg-cyber-danger/20 text-cyber-danger border border-cyber-danger/40'
                      : 'bg-cyber-card text-cyber-muted border border-cyber-border hover:border-cyber-border2'
                  }`}
                >
                  {f === 'all' ? 'All' : f === 'high-risk' ? 'High Risk' : f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="px-2.5 py-1.5 text-xs bg-cyber-card border border-cyber-border rounded-lg text-cyber-text focus:outline-none focus:border-cyber-primary/50 cursor-pointer"
            >
              <option value="trust">Sort: Trust Score</option>
              <option value="traffic">Sort: Traffic</option>
              <option value="name">Sort: Name</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-cyber-surface border-b border-cyber-border z-10">
              <tr>
                <th className="px-4 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Device</th>
                <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Type</th>
                <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">IP Address</th>
                {!selected && <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Vendor</th>}
                <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Trust</th>
                <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Risk</th>
                {!selected && <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Traffic</th>}
                <th className="px-3 py-2.5 text-left text-cyber-muted uppercase tracking-wider font-medium">Last Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border/50">
              {filtered.map(device => {
                const isActive = selected?.id === device.id;
                const trustColor =
                  device.riskLevel === 'safe' ? '#10b981'
                  : device.riskLevel === 'suspicious' ? '#f59e0b'
                  : '#ef4444';

                return (
                  <tr
                    key={device.id}
                    onClick={() => setSelected(isActive ? null : device)}
                    className={`cursor-pointer transition-colors hover:bg-cyber-card/60 ${
                      isActive ? 'bg-cyber-primary/5 border-l-2 border-cyber-primary' : ''
                    } ${device.isNew ? 'bg-cyber-safe/5 animate-pulse' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">{DEVICE_ICONS[device.type] || '📟'}</span>
                        <div>
                          <div className="font-medium text-cyber-text">{device.name}</div>
                          {device.isNew && (
                            <span className="text-[10px] text-cyber-safe font-bold">NEW</span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-cyber-dim">{device.type}</td>
                    <td className="px-3 py-3 font-mono text-cyber-primary">{device.ip}</td>
                    {!selected && <td className="px-3 py-3 text-cyber-dim">{device.vendor}</td>}
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-cyber-bg rounded-full h-1.5">
                          <div
                            className="h-1.5 rounded-full transition-all duration-500"
                            style={{ width: `${device.trustScore}%`, backgroundColor: trustColor }}
                          />
                        </div>
                        <span className="font-bold" style={{ color: trustColor }}>
                          {Math.round(device.trustScore)}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge level={device.riskLevel} size="sm" />
                    </td>
                    {!selected && (
                      <td className="px-3 py-3">
                        <span className="text-cyber-dim">{device.trafficRate.toFixed(1)} Mbps</span>
                      </td>
                    )}
                    <td className="px-3 py-3 text-cyber-muted">{formatLastSeen(device.lastSeen)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center h-40 text-cyber-muted">
              <Monitor size={32} className="mb-2 opacity-30" />
              <p className="text-sm">No devices match your filters</p>
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="w-[40%] h-full">
          <DeviceDetailPanel
            device={selected}
            onClose={() => setSelected(null)}
          />
        </div>
      )}
    </div>
  );
}
