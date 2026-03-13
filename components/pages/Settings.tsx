'use client';

import { useState } from 'react';
import { Settings as SettingsIcon, Bell, Shield, Network, Eye, Save, RotateCcw, ChevronRight } from 'lucide-react';

interface SettingItem {
  id: string;
  label: string;
  description: string;
  type: 'toggle' | 'slider' | 'select' | 'number';
  value: boolean | number | string;
  min?: number;
  max?: number;
  options?: string[];
}

interface SettingGroup {
  id: string;
  label: string;
  icon: React.ReactNode;
  settings: SettingItem[];
}

const INITIAL_GROUPS: SettingGroup[] = [
  {
    id: 'alerts',
    label: 'Alert Configuration',
    icon: <Bell size={16} className="text-cyber-danger" />,
    settings: [
      {
        id: 'alert_sensitivity',
        label: 'Alert Sensitivity',
        description: 'Controls how aggressively the system generates alerts',
        type: 'select',
        value: 'Medium',
        options: ['Low', 'Medium', 'High', 'Critical Only'],
      },
      {
        id: 'auto_alerts',
        label: 'Automatic Alerts',
        description: 'Generate alerts automatically from behavioral analysis',
        type: 'toggle',
        value: true,
      },
      {
        id: 'email_notifications',
        label: 'Email Notifications',
        description: 'Send alerts to configured email addresses',
        type: 'toggle',
        value: false,
      },
      {
        id: 'alert_cooldown',
        label: 'Alert Cooldown (seconds)',
        description: 'Minimum time between repeated alerts for the same device',
        type: 'number',
        value: 300,
        min: 60,
        max: 3600,
      },
    ],
  },
  {
    id: 'trust',
    label: 'Trust Score Thresholds',
    icon: <Shield size={16} className="text-cyber-primary" />,
    settings: [
      {
        id: 'safe_threshold',
        label: 'Safe Threshold',
        description: 'Minimum trust score to classify a device as safe (0–100)',
        type: 'slider',
        value: 70,
        min: 50,
        max: 95,
      },
      {
        id: 'suspicious_threshold',
        label: 'Suspicious Threshold',
        description: 'Minimum trust score before device is flagged as suspicious',
        type: 'slider',
        value: 40,
        min: 10,
        max: 70,
      },
      {
        id: 'auto_quarantine',
        label: 'Auto-Quarantine High Risk',
        description: 'Automatically isolate devices when trust score falls below 20',
        type: 'toggle',
        value: false,
      },
      {
        id: 'trust_decay',
        label: 'Trust Score Decay Rate',
        description: 'How quickly trust score decreases with each anomaly',
        type: 'select',
        value: 'Moderate',
        options: ['Slow', 'Moderate', 'Fast', 'Aggressive'],
      },
    ],
  },
  {
    id: 'monitoring',
    label: 'Network Monitoring',
    icon: <Network size={16} className="text-cyber-safe" />,
    settings: [
      {
        id: 'scan_interval',
        label: 'Scan Interval (seconds)',
        description: 'How often the system polls devices for behavioral data',
        type: 'slider',
        value: 30,
        min: 5,
        max: 300,
      },
      {
        id: 'deep_inspection',
        label: 'Deep Packet Inspection',
        description: 'Enable protocol-level traffic analysis (higher CPU usage)',
        type: 'toggle',
        value: true,
      },
      {
        id: 'baseline_learning',
        label: 'Behavioral Baseline Learning',
        description: 'Automatically learn normal behavior for each device',
        type: 'toggle',
        value: true,
      },
      {
        id: 'max_devices',
        label: 'Max Tracked Devices',
        description: 'Maximum number of devices to track simultaneously',
        type: 'number',
        value: 500,
        min: 50,
        max: 10000,
      },
    ],
  },
  {
    id: 'display',
    label: 'Display & Interface',
    icon: <Eye size={16} className="text-cyber-suspicious" />,
    settings: [
      {
        id: 'refresh_rate',
        label: 'Dashboard Refresh Rate',
        description: 'How frequently the dashboard refreshes live data',
        type: 'select',
        value: 'Every 3 seconds',
        options: ['Every second', 'Every 3 seconds', 'Every 5 seconds', 'Every 10 seconds'],
      },
      {
        id: 'show_resolved',
        label: 'Show Resolved Alerts',
        description: 'Display previously resolved alerts in the alerts panel',
        type: 'toggle',
        value: true,
      },
      {
        id: 'animate_map',
        label: 'Network Map Animations',
        description: 'Enable traffic flow animations on the network topology map',
        type: 'toggle',
        value: true,
      },
      {
        id: 'compact_mode',
        label: 'Compact Mode',
        description: 'Use compact view for device lists and alerts',
        type: 'toggle',
        value: false,
      },
    ],
  },
];

export default function Settings() {
  const [groups, setGroups] = useState(INITIAL_GROUPS);
  const [saved, setSaved] = useState(false);

  const updateSetting = (groupId: string, settingId: string, value: boolean | number | string) => {
    setGroups(prev => prev.map(g =>
      g.id === groupId
        ? {
          ...g,
          settings: g.settings.map(s =>
            s.id === settingId ? { ...s, value } : s
          ),
        }
        : g
    ));
    setSaved(false);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setGroups(INITIAL_GROUPS);
    setSaved(false);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-cyber-primary neon-text flex items-center gap-2">
              <SettingsIcon size={18} /> System Settings
            </h1>
            <p className="text-xs text-cyber-muted">Configure monitoring policies and alert thresholds</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-cyber-card border border-cyber-border rounded-lg text-cyber-muted hover:text-cyber-text transition-colors"
            >
              <RotateCcw size={12} /> Reset
            </button>
            <button
              onClick={handleSave}
              className={`flex items-center gap-1.5 px-4 py-1.5 text-xs rounded-lg font-medium transition-all ${
                saved
                  ? 'bg-cyber-safe/20 border border-cyber-safe/40 text-cyber-safe'
                  : 'bg-cyber-primary/15 border border-cyber-primary/40 text-cyber-primary hover:bg-cyber-primary/25'
              }`}
            >
              <Save size={12} /> {saved ? 'Saved!' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Settings content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl space-y-6">
          {groups.map(group => (
            <div key={group.id} className="cyber-card neon-border overflow-hidden">
              <div className="px-5 py-3 border-b border-cyber-border bg-cyber-bg/30 flex items-center gap-2">
                {group.icon}
                <h2 className="text-sm font-bold text-cyber-dim">{group.label}</h2>
              </div>
              <div className="divide-y divide-cyber-border/50">
                {group.settings.map(setting => (
                  <div key={setting.id} className="px-5 py-4 flex items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-cyber-text">{setting.label}</div>
                      <div className="text-xs text-cyber-muted mt-0.5">{setting.description}</div>
                    </div>

                    <div className="flex-shrink-0">
                      {setting.type === 'toggle' && (
                        <button
                          onClick={() => updateSetting(group.id, setting.id, !setting.value)}
                          className={`relative w-11 h-6 rounded-full transition-colors ${
                            setting.value ? 'bg-cyber-primary' : 'bg-cyber-border'
                          }`}
                        >
                          <span
                            className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform shadow ${
                              setting.value ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      )}

                      {setting.type === 'slider' && (
                        <div className="flex items-center gap-3 w-48">
                          <input
                            type="range"
                            min={setting.min}
                            max={setting.max}
                            value={setting.value as number}
                            onChange={e => updateSetting(group.id, setting.id, Number(e.target.value))}
                            className="flex-1 h-1.5 appearance-none rounded-full bg-cyber-border cursor-pointer accent-cyber-primary"
                          />
                          <span className="text-xs font-mono text-cyber-primary w-8 text-right">
                            {setting.value}
                          </span>
                        </div>
                      )}

                      {setting.type === 'select' && (
                        <select
                          value={setting.value as string}
                          onChange={e => updateSetting(group.id, setting.id, e.target.value)}
                          className="px-3 py-1.5 text-xs bg-cyber-bg border border-cyber-border rounded-lg text-cyber-text focus:outline-none focus:border-cyber-primary/50 cursor-pointer"
                        >
                          {setting.options?.map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                          ))}
                        </select>
                      )}

                      {setting.type === 'number' && (
                        <input
                          type="number"
                          min={setting.min}
                          max={setting.max}
                          value={setting.value as number}
                          onChange={e => updateSetting(group.id, setting.id, Number(e.target.value))}
                          className="w-24 px-3 py-1.5 text-xs bg-cyber-bg border border-cyber-border rounded-lg text-cyber-primary font-mono text-right focus:outline-none focus:border-cyber-primary/50"
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* System info card */}
          <div className="cyber-card neon-border p-5">
            <h2 className="text-sm font-bold text-cyber-dim mb-4 flex items-center gap-2">
              <SettingsIcon size={14} className="text-cyber-primary" />
              System Information
            </h2>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {[
                ['Platform', 'IoT SecureNet v2.4.1'],
                ['Engine', 'Behavioral Analysis Engine v3.0'],
                ['Database', 'Time-series DB (In-Memory)'],
                ['ML Model', 'Anomaly Detection v1.8'],
                ['Last Update', 'March 13, 2026'],
                ['License', 'Enterprise Edition'],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-2 p-2 bg-cyber-bg/40 rounded">
                  <span className="text-cyber-muted">{label}</span>
                  <span className="text-cyber-dim font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
