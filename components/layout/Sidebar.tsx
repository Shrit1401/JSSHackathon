'use client';

import { useSimulation } from '@/lib/store';
import { NavSection } from '@/lib/types';
import {
  LayoutDashboard,
  Monitor,
  Network,
  Bell,
  Clock,
  Bot,
  Settings,
  Shield,
  Wifi,
  Activity,
} from 'lucide-react';

interface NavItem {
  id: NavSection;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
  { id: 'devices', label: 'Devices', icon: <Monitor size={18} /> },
  { id: 'network-map', label: 'Network Map', icon: <Network size={18} /> },
  { id: 'alerts', label: 'Alerts', icon: <Bell size={18} /> },
  { id: 'events', label: 'Events Timeline', icon: <Clock size={18} /> },
  { id: 'ai-assistant', label: 'AI Security Assistant', icon: <Bot size={18} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={18} /> },
];

export default function Sidebar() {
  const { activeNav, setActiveNav, unreadAlerts, devices } = useSimulation();

  const highRisk = devices.filter(d => d.riskLevel === 'high-risk').length;
  const suspicious = devices.filter(d => d.riskLevel === 'suspicious').length;

  return (
    <aside className="w-64 h-screen flex flex-col flex-shrink-0 bg-cyber-surface border-r border-cyber-border">
      {/* Logo / Brand */}
      <div className="px-5 py-4 border-b border-cyber-border">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Shield size={28} className="text-cyber-primary" />
            <span
              className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyber-safe blink"
              title="System Active"
            />
          </div>
          <div>
            <div className="text-sm font-bold text-cyber-primary neon-text tracking-wider">
              IoT SecureNet
            </div>
            <div className="text-xs text-cyber-muted">SOC Dashboard v2.4</div>
          </div>
        </div>
      </div>

      {/* System status strip */}
      <div className="px-4 py-2.5 border-b border-cyber-border bg-cyber-bg/40">
        <div className="flex items-center gap-1.5 text-xs">
          <Activity size={11} className="text-cyber-safe" />
          <span className="text-cyber-safe font-medium">SYSTEM ACTIVE</span>
          <span className="mx-1 text-cyber-border">|</span>
          <Wifi size={11} className="text-cyber-primary" />
          <span className="text-cyber-dim">{devices.length} devices</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map(item => {
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                transition-all duration-200 group relative
                ${isActive
                  ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30'
                  : 'text-cyber-dim hover:text-cyber-text hover:bg-cyber-card'
                }
              `}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-cyber-primary rounded-r-full" />
              )}
              <span className={isActive ? 'text-cyber-primary' : 'text-cyber-muted group-hover:text-cyber-dim'}>
                {item.icon}
              </span>
              <span className="flex-1 text-left">{item.label}</span>

              {/* Badge for alerts */}
              {item.id === 'alerts' && unreadAlerts > 0 && (
                <span className="flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-cyber-danger text-white text-xs font-bold animate-pulse">
                  {unreadAlerts}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Threat summary */}
      <div className="px-4 py-3 border-t border-cyber-border space-y-2">
        <div className="text-xs text-cyber-muted uppercase tracking-wider font-semibold mb-2">
          Threat Summary
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 text-cyber-danger">
            <span className="w-2 h-2 rounded-full bg-cyber-danger animate-pulse-red inline-block" />
            High Risk
          </span>
          <span className="font-bold text-cyber-danger">{highRisk}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 text-cyber-suspicious">
            <span className="w-2 h-2 rounded-full bg-cyber-suspicious animate-pulse-yellow inline-block" />
            Suspicious
          </span>
          <span className="font-bold text-cyber-suspicious">{suspicious}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 text-cyber-safe">
            <span className="w-2 h-2 rounded-full bg-cyber-safe inline-block" />
            Safe
          </span>
          <span className="font-bold text-cyber-safe">{devices.length - highRisk - suspicious}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-cyber-border">
        <div className="text-xs text-cyber-muted">
          Last scan: <span className="text-cyber-dim">just now</span>
        </div>
      </div>
    </aside>
  );
}
