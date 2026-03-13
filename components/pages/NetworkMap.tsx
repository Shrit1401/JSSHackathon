'use client';

import { useSimulation } from '@/lib/store';
import { Device } from '@/lib/types';
import { useState, useMemo, useRef, useEffect } from 'react';
import { Info, Maximize2 } from 'lucide-react';
import StatusBadge from '../shared/StatusBadge';

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

function getRiskColor(level: string) {
  if (level === 'safe') return '#10b981';
  if (level === 'suspicious') return '#f59e0b';
  return '#ef4444';
}

function getRiskGlow(level: string) {
  if (level === 'safe') return 'drop-shadow(0 0 6px #10b98180)';
  if (level === 'suspicious') return 'drop-shadow(0 0 8px #f59e0b80)';
  return 'drop-shadow(0 0 12px #ef444480)';
}

interface NodePosition {
  device: Device;
  x: number;
  y: number;
}

export default function NetworkMap() {
  const { devices } = useSimulation();
  const [hoveredDevice, setHoveredDevice] = useState<Device | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const tickRef = useRef(0);
  const [, forceUpdate] = useState(0);

  // Animate traffic dots
  useEffect(() => {
    const id = setInterval(() => {
      tickRef.current = (tickRef.current + 1) % 100;
      forceUpdate(n => n + 1);
    }, 50);
    return () => clearInterval(id);
  }, []);

  // Measure SVG container
  useEffect(() => {
    const el = svgRef.current?.parentElement;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setDims({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const cx = dims.w / 2;
  const cy = dims.h / 2;

  // Layout: router in center, devices in concentric circles
  const nodePositions = useMemo((): NodePosition[] => {
    const nonRouter = devices.filter(d => d.type !== 'Router');
    const router = devices.find(d => d.type === 'Router');

    const innerCount = Math.min(8, nonRouter.length);
    const outerDevices = nonRouter.slice(innerCount);
    const innerDevices = nonRouter.slice(0, innerCount);

    const innerR = Math.min(dims.w, dims.h) * 0.28;
    const outerR = Math.min(dims.w, dims.h) * 0.42;

    const positions: NodePosition[] = [];

    if (router) {
      positions.push({ device: router, x: cx, y: cy });
    }

    innerDevices.forEach((dev, i) => {
      const angle = (2 * Math.PI * i) / innerDevices.length - Math.PI / 2;
      positions.push({
        device: dev,
        x: cx + innerR * Math.cos(angle),
        y: cy + innerR * Math.sin(angle),
      });
    });

    outerDevices.forEach((dev, i) => {
      const angle = (2 * Math.PI * i) / outerDevices.length - Math.PI / 2;
      positions.push({
        device: dev,
        x: cx + outerR * Math.cos(angle),
        y: cy + outerR * Math.sin(angle),
      });
    });

    return positions;
  }, [devices, cx, cy, dims]);

  const routerPos = nodePositions.find(n => n.device.type === 'Router');

  const infoDevice = selectedDevice || hoveredDevice;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-lg font-bold text-cyber-primary neon-text">Network Topology Map</h1>
          <p className="text-xs text-cyber-muted">Live visualization — {devices.length} devices connected</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <LegendItem color="#10b981" label="Safe" />
          <LegendItem color="#f59e0b" label="Suspicious" />
          <LegendItem color="#ef4444" label="High Risk" pulse />
          <LegendItem color="#00d4ff" label="Router" />
        </div>
      </div>

      <div className="flex-1 relative overflow-hidden">
        {/* SVG Map */}
        <div className="absolute inset-0">
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            style={{ background: 'transparent' }}
          >
            <defs>
              {/* Glow filters */}
              <filter id="glow-safe" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              <filter id="glow-danger" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              {/* Animated traffic gradient */}
              <linearGradient id="traffic-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00d4ff" stopOpacity="0" />
                <stop offset="50%" stopColor="#00d4ff" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Connection lines */}
            {routerPos && nodePositions
              .filter(n => n.device.type !== 'Router')
              .map(node => {
                const color = getRiskColor(node.device.riskLevel);
                const dashLen = Math.sqrt(
                  Math.pow(node.x - routerPos.x, 2) + Math.pow(node.y - routerPos.y, 2)
                );
                const speed = node.device.riskLevel === 'high-risk' ? 0.5 : 1.5;

                return (
                  <g key={`line-${node.device.id}`}>
                    {/* Background line */}
                    <line
                      x1={routerPos.x}
                      y1={routerPos.y}
                      x2={node.x}
                      y2={node.y}
                      stroke={color}
                      strokeWidth="1"
                      strokeOpacity="0.2"
                    />
                    {/* Animated traffic dash */}
                    <line
                      x1={routerPos.x}
                      y1={routerPos.y}
                      x2={node.x}
                      y2={node.y}
                      stroke={color}
                      strokeWidth="1.5"
                      strokeOpacity="0.6"
                      strokeDasharray="12 20"
                      strokeDashoffset={-(tickRef.current * speed * 3) % 32}
                    />
                    {/* Traveling dot */}
                    <TrafficDot
                      x1={routerPos.x}
                      y1={routerPos.y}
                      x2={node.x}
                      y2={node.y}
                      color={color}
                      progress={(tickRef.current * speed * 0.02) % 1}
                    />
                  </g>
                );
              })}

            {/* Device nodes */}
            {nodePositions.map(node => {
              const isRouter = node.device.type === 'Router';
              const color = isRouter ? '#00d4ff' : getRiskColor(node.device.riskLevel);
              const r = isRouter ? 28 : 20;
              const isHighRisk = node.device.riskLevel === 'high-risk';
              const isSuspicious = node.device.riskLevel === 'suspicious';
              const isSelected = selectedDevice?.id === node.device.id;

              return (
                <g
                  key={`node-${node.device.id}`}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={() => setSelectedDevice(prev => prev?.id === node.device.id ? null : node.device)}
                  onMouseEnter={() => setHoveredDevice(node.device)}
                  onMouseLeave={() => setHoveredDevice(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Pulse ring for risky devices */}
                  {isHighRisk && (
                    <>
                      <circle r={r + 8} fill="none" stroke="#ef4444" strokeWidth="1" opacity="0.4">
                        <animate attributeName="r" values={`${r + 4};${r + 18};${r + 4}`} dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.5;0;0.5" dur="2s" repeatCount="indefinite" />
                      </circle>
                      <circle r={r + 4} fill="none" stroke="#ef4444" strokeWidth="1.5" opacity="0.6">
                        <animate attributeName="r" values={`${r};${r + 12};${r}`} dur="2s" begin="0.5s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" begin="0.5s" repeatCount="indefinite" />
                      </circle>
                    </>
                  )}
                  {isSuspicious && (
                    <circle r={r + 5} fill="none" stroke="#f59e0b" strokeWidth="1" opacity="0.4">
                      <animate attributeName="r" values={`${r + 2};${r + 10};${r + 2}`} dur="3s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.4;0;0.4" dur="3s" repeatCount="indefinite" />
                    </circle>
                  )}

                  {/* Selection ring */}
                  {isSelected && (
                    <circle r={r + 6} fill="none" stroke={color} strokeWidth="2" strokeDasharray="4 3" opacity="0.8">
                      <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0"
                        to="360"
                        dur="4s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  )}

                  {/* Node background */}
                  <circle
                    r={r}
                    fill={`${color}15`}
                    stroke={color}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    style={{ filter: getRiskGlow(node.device.riskLevel) }}
                  />

                  {/* Device icon */}
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={isRouter ? 18 : 14}
                    style={{ userSelect: 'none' }}
                  >
                    {isRouter ? '📡' : DEVICE_ICONS[node.device.type] || '📟'}
                  </text>

                  {/* Trust score badge */}
                  {!isRouter && (
                    <g transform={`translate(${r - 4}, ${-r + 4})`}>
                      <circle r={9} fill={color} />
                      <text
                        textAnchor="middle"
                        dominantBaseline="central"
                        fontSize={8}
                        fontWeight="bold"
                        fill="white"
                      >
                        {Math.round(node.device.trustScore)}
                      </text>
                    </g>
                  )}

                  {/* Device name */}
                  <text
                    y={r + 14}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#94a3b8"
                    fontFamily="monospace"
                    style={{ userSelect: 'none' }}
                  >
                    {node.device.name.length > 14
                      ? node.device.name.substring(0, 13) + '…'
                      : node.device.name}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Info Panel overlay */}
        {infoDevice && (
          <div className="absolute top-4 right-4 w-64 cyber-card p-4 border border-cyber-border neon-border fade-in-up z-10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">{DEVICE_ICONS[infoDevice.type] || '📟'}</span>
                <div>
                  <div className="text-sm font-bold text-cyber-text">{infoDevice.name}</div>
                  <div className="text-xs text-cyber-muted">{infoDevice.type}</div>
                </div>
              </div>
              <StatusBadge level={infoDevice.riskLevel} size="sm" />
            </div>
            <div className="space-y-1.5 text-xs">
              <InfoRow label="IP" value={infoDevice.ip} />
              <InfoRow label="Vendor" value={infoDevice.vendor} />
              <InfoRow label="Trust" value={`${Math.round(infoDevice.trustScore)}/100`} color={getRiskColor(infoDevice.riskLevel)} />
              <InfoRow label="Traffic" value={`${infoDevice.trafficRate.toFixed(1)} Mbps`} />
            </div>
            {infoDevice.flagReason && (
              <div className="mt-2 text-xs text-cyber-danger/80 border-t border-cyber-border pt-2">
                {infoDevice.flagReason.substring(0, 80)}…
              </div>
            )}
            {selectedDevice && (
              <button
                onClick={() => setSelectedDevice(null)}
                className="mt-2 text-xs text-cyber-muted hover:text-cyber-text"
              >
                Click to deselect
              </button>
            )}
          </div>
        )}

        {/* Stats overlay bottom-left */}
        <div className="absolute bottom-4 left-4 flex gap-2">
          {[
            { label: 'Safe', color: '#10b981', count: devices.filter(d => d.riskLevel === 'safe').length },
            { label: 'Suspicious', color: '#f59e0b', count: devices.filter(d => d.riskLevel === 'suspicious').length },
            { label: 'High Risk', color: '#ef4444', count: devices.filter(d => d.riskLevel === 'high-risk').length },
          ].map(s => (
            <div key={s.label} className="cyber-card px-3 py-1.5 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: s.color }} />
              <span className="text-cyber-muted">{s.label}:</span>
              <span className="font-bold" style={{ color: s.color }}>{s.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TrafficDot({ x1, y1, x2, y2, color, progress }: {
  x1: number; y1: number; x2: number; y2: number; color: string; progress: number;
}) {
  const x = x1 + (x2 - x1) * progress;
  const y = y1 + (y2 - y1) * progress;
  return (
    <circle
      cx={x}
      cy={y}
      r={3}
      fill={color}
      opacity={0.9}
      style={{ filter: `drop-shadow(0 0 4px ${color})` }}
    />
  );
}

function LegendItem({ color, label, pulse }: { color: string; label: string; pulse?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`w-2.5 h-2.5 rounded-full ${pulse ? 'animate-pulse' : ''}`}
        style={{ background: color }}
      />
      <span className="text-cyber-muted">{label}</span>
    </div>
  );
}

function InfoRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-cyber-muted">{label}</span>
      <span className="font-mono" style={{ color: color || '#94a3b8' }}>{value}</span>
    </div>
  );
}
