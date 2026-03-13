export type RiskLevel = 'safe' | 'suspicious' | 'high-risk';

export type DeviceType =
  | 'Laptop'
  | 'Phone'
  | 'Printer'
  | 'Smart TV'
  | 'Security Camera'
  | 'Router'
  | 'IoT Sensor'
  | 'Server'
  | 'Tablet';

export interface ProtocolUsage {
  protocol: string;
  percentage: number;
}

export interface TimeSeriesPoint {
  time: string;
  value: number;
}

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  ip: string;
  mac: string;
  vendor: string;
  trustScore: number; // 0-100
  trafficRate: number; // Mbps
  riskLevel: RiskLevel;
  lastSeen: Date;
  ports: number[];
  protocolUsage: ProtocolUsage[];
  trustHistory: TimeSeriesPoint[];
  trafficHistory: TimeSeriesPoint[];
  os?: string;
  location?: string;
  isNew?: boolean;
  flagReason?: string;
}

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  type: string;
  deviceId: string;
  deviceName: string;
  severity: AlertSeverity;
  timestamp: Date;
  message: string;
  read: boolean;
}

export type EventType =
  | 'device_joined'
  | 'device_left'
  | 'traffic_spike'
  | 'trust_update'
  | 'anomaly'
  | 'policy_violation'
  | 'new_connection'
  | 'scan_detected'
  | 'alert_generated';

export interface NetworkEvent {
  id: string;
  time: Date;
  deviceId: string;
  deviceName: string;
  type: EventType;
  description: string;
}

export type NavSection =
  | 'overview'
  | 'devices'
  | 'network-map'
  | 'alerts'
  | 'events'
  | 'ai-assistant'
  | 'settings';

export interface SimulationState {
  devices: Device[];
  alerts: Alert[];
  events: NetworkEvent[];
  activeNav: NavSection;
  setActiveNav: (nav: NavSection) => void;
  unreadAlerts: number;
}
