'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { Device, Alert, NetworkEvent, NavSection, RiskLevel, EventType } from './types';
import { initialDevices, initialAlerts, initialEvents } from './mockData';

interface SimulationContextType {
  devices: Device[];
  alerts: Alert[];
  events: NetworkEvent[];
  activeNav: NavSection;
  setActiveNav: (nav: NavSection) => void;
  unreadAlerts: number;
  markAlertsRead: () => void;
}

const SimulationContext = createContext<SimulationContextType | null>(null);

function getRiskLevel(score: number): RiskLevel {
  if (score >= 70) return 'safe';
  if (score >= 40) return 'suspicious';
  return 'high-risk';
}

function generateId() {
  return Math.random().toString(36).substring(2, 11);
}

function formatTime(d: Date) {
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

const NEW_DEVICE_TEMPLATES = [
  { name: 'LAPTOP-TEMP-', type: 'Laptop' as const, vendor: 'HP Inc.', ip: '192.168.1.' },
  { name: 'PHONE-NEW-', type: 'Phone' as const, vendor: 'Google LLC', ip: '192.168.2.' },
  { name: 'SENSOR-NEW-', type: 'IoT Sensor' as const, vendor: 'Arduino', ip: '192.168.1.' },
  { name: 'TABLET-NEW-', type: 'Tablet' as const, vendor: 'Lenovo', ip: '192.168.3.' },
];

const ANOMALY_MESSAGES = [
  'Traffic spike detected',
  'Unusual protocol activity observed',
  'Beacon interval anomaly detected',
  'DNS query flood detected',
  'ARP spoofing attempt detected',
  'Excessive connection attempts logged',
];

const POLICY_MESSAGES = [
  'Unauthorized port access attempted',
  'Data exfiltration pattern detected',
  'Security policy bypass attempted',
  'Unencrypted sensitive data transmission',
  'Prohibited service access detected',
];

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [devices, setDevices] = useState<Device[]>(initialDevices);
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts);
  const [events, setEvents] = useState<NetworkEvent[]>(initialEvents);
  const [activeNav, setActiveNav] = useState<NavSection>('overview');
  const [unreadAlerts, setUnreadAlerts] = useState(3);
  const tickRef = useRef(0);
  const deviceCounterRef = useRef(30);

  const addAlert = useCallback((alert: Omit<Alert, 'id'>) => {
    const newAlert = { ...alert, id: `alert-${generateId()}` };
    setAlerts(prev => [newAlert, ...prev].slice(0, 50));
    setUnreadAlerts(prev => prev + 1);
  }, []);

  const addEvent = useCallback((event: Omit<NetworkEvent, 'id'>) => {
    const newEvent = { ...event, id: `evt-${generateId()}` };
    setEvents(prev => [newEvent, ...prev].slice(0, 100));
  }, []);

  const markAlertsRead = useCallback(() => {
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
    setUnreadAlerts(0);
  }, []);

  useEffect(() => {
    const tick = setInterval(() => {
      tickRef.current++;
      const now = new Date();

      setDevices(prevDevices => {
        const updated = [...prevDevices];
        // Pick 1-3 random devices to update
        const numToUpdate = Math.floor(Math.random() * 3) + 1;
        const indices = new Set<number>();
        while (indices.size < numToUpdate) {
          indices.add(Math.floor(Math.random() * updated.length));
        }

        indices.forEach(i => {
          const device = { ...updated[i] };
          const roll = Math.random();

          if (roll < 0.3) {
            // Trust score change
            const delta = (Math.random() - 0.6) * 8; // slightly biased negative
            const newScore = Math.max(5, Math.min(100, device.trustScore + delta));
            const oldRisk = device.riskLevel;
            const newRisk = getRiskLevel(newScore);

            device.trustScore = Math.round(newScore * 10) / 10;
            device.riskLevel = newRisk;

            // Update trust history
            device.trustHistory = [
              ...device.trustHistory.slice(-28),
              { time: formatTime(now), value: device.trustScore },
            ];

            // Generate event
            if (Math.abs(delta) > 4) {
              addEvent({
                time: now,
                deviceId: device.id,
                deviceName: device.name,
                type: 'trust_update',
                description: `Trust score updated: ${Math.round(device.trustScore - delta)} → ${Math.round(device.trustScore)}`,
              });
            }

            // Generate alert on risk level change to worse
            if (oldRisk === 'safe' && newRisk === 'suspicious') {
              addAlert({
                type: 'Trust Score Drop',
                deviceId: device.id,
                deviceName: device.name,
                severity: 'medium',
                timestamp: now,
                message: `${device.name} trust score dropped to ${Math.round(device.trustScore)}. Device classified as suspicious.`,
                read: false,
              });
              device.flagReason = `Trust score dropped to ${Math.round(device.trustScore)}. Behavioral anomaly detected.`;
            } else if (newRisk === 'high-risk' && oldRisk !== 'high-risk') {
              addAlert({
                type: 'High Risk Device',
                deviceId: device.id,
                deviceName: device.name,
                severity: 'critical',
                timestamp: now,
                message: `CRITICAL: ${device.name} trust score is ${Math.round(device.trustScore)}. Device classified as HIGH RISK.`,
                read: false,
              });
              device.flagReason = `Trust score critically low at ${Math.round(device.trustScore)}. Immediate investigation required.`;
            }
          } else if (roll < 0.6) {
            // Traffic rate change
            const multiplier = 0.7 + Math.random() * 0.9;
            const newRate = Math.max(0.1, device.trafficRate * multiplier);
            device.trafficRate = Math.round(newRate * 10) / 10;

            device.trafficHistory = [
              ...device.trafficHistory.slice(-28),
              { time: formatTime(now), value: device.trafficRate },
            ];

            // Anomaly alert if traffic spikes significantly
            if (multiplier > 1.5 && device.trafficRate > 10) {
              const msg = ANOMALY_MESSAGES[Math.floor(Math.random() * ANOMALY_MESSAGES.length)];
              addEvent({
                time: now,
                deviceId: device.id,
                deviceName: device.name,
                type: 'anomaly',
                description: `${msg}: ${device.trafficRate.toFixed(1)} Mbps`,
              });
              if (Math.random() < 0.4) {
                addAlert({
                  type: 'Traffic Anomaly',
                  deviceId: device.id,
                  deviceName: device.name,
                  severity: 'high',
                  timestamp: now,
                  message: `${msg} on ${device.name}. Traffic rate: ${device.trafficRate.toFixed(1)} Mbps.`,
                  read: false,
                });
                device.trustScore = Math.max(5, device.trustScore - Math.random() * 8);
                device.riskLevel = getRiskLevel(device.trustScore);
              }
            }
          } else if (roll < 0.75) {
            // Policy violation event
            if (Math.random() < 0.3) {
              const msg = POLICY_MESSAGES[Math.floor(Math.random() * POLICY_MESSAGES.length)];
              addEvent({
                time: now,
                deviceId: device.id,
                deviceName: device.name,
                type: 'policy_violation',
                description: msg,
              });
              if (Math.random() < 0.3) {
                addAlert({
                  type: 'Policy Violation',
                  deviceId: device.id,
                  deviceName: device.name,
                  severity: 'medium',
                  timestamp: now,
                  message: `${msg} — ${device.name}`,
                  read: false,
                });
              }
            }
          }

          device.lastSeen = now;
          updated[i] = device;
        });

        return updated;
      });

      // Occasionally add a new device
      if (tickRef.current % 20 === 0) {
        const template = NEW_DEVICE_TEMPLATES[Math.floor(Math.random() * NEW_DEVICE_TEMPLATES.length)];
        deviceCounterRef.current++;
        const counter = deviceCounterRef.current;
        const score = 50 + Math.floor(Math.random() * 45);
        const newDevice: Device = {
          id: `dev-new-${counter}`,
          name: `${template.name}${counter}`,
          type: template.type,
          ip: `${template.ip}${counter % 254 + 2}`,
          mac: `BB:CC:DD:EE:FF:${counter.toString(16).padStart(2, '0').toUpperCase()}`,
          vendor: template.vendor,
          trustScore: score,
          trafficRate: Math.round(Math.random() * 15 * 10) / 10,
          riskLevel: getRiskLevel(score),
          lastSeen: now,
          ports: [443, 80],
          protocolUsage: [
            { protocol: 'HTTPS', percentage: 80 },
            { protocol: 'DNS', percentage: 20 },
          ],
          trustHistory: Array.from({ length: 10 }, (_, i) => ({
            time: formatTime(new Date(now.getTime() - (10 - i) * 30000)),
            value: score,
          })),
          trafficHistory: Array.from({ length: 10 }, (_, i) => ({
            time: formatTime(new Date(now.getTime() - (10 - i) * 30000)),
            value: Math.random() * 5,
          })),
          isNew: true,
        };

        setDevices(prev => [...prev, newDevice]);
        addEvent({
          time: now,
          deviceId: newDevice.id,
          deviceName: newDevice.name,
          type: 'device_joined',
          description: `New ${newDevice.type} connected from ${newDevice.ip} (${newDevice.vendor})`,
        });
        addAlert({
          type: 'New Device Detected',
          deviceId: newDevice.id,
          deviceName: newDevice.name,
          severity: 'low',
          timestamp: now,
          message: `New device ${newDevice.name} joined the network from ${newDevice.ip}.`,
          read: false,
        });

        // Remove new flag after a few seconds
        setTimeout(() => {
          setDevices(prev =>
            prev.map(d => d.id === newDevice.id ? { ...d, isNew: false } : d)
          );
        }, 5000);
      }
    }, 3000);

    return () => clearInterval(tick);
  }, [addAlert, addEvent]);

  const value: SimulationContextType = {
    devices,
    alerts,
    events,
    activeNav,
    setActiveNav,
    unreadAlerts,
    markAlertsRead,
  };

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider');
  return ctx;
}
