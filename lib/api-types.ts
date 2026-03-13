export type RiskLevelAPI = "SAFE" | "LOW" | "MEDIUM" | "HIGH"

export type DeviceStatus = "online" | "offline" | "compromised"

export type AttackType =
  | "TRAFFIC_SPIKE"
  | "POLICY_VIOLATION"
  | "NEW_DESTINATION"
  | "BACKDOOR"
  | "DATA_EXFILTRATION"

export interface OverviewStats {
  total_devices: number
  safe: number
  low: number
  medium: number
  high: number
  online: number
  offline: number
}

export interface DeviceSummary {
  id: string
  name: string
  device_type: string
  ip_address: string
  vendor: string
  trust_score: number
  risk_level: RiskLevelAPI
  traffic_rate: number
  status: DeviceStatus
  last_seen: string
}

export interface DeviceDetail extends DeviceSummary {
  created_at: string
  open_ports: string[]
  protocol_usage: Record<string, number>
  security_explanation: string
}

export interface ExplainResponse {
  device_id: string
  device_name: string
  risk_level: RiskLevelAPI
  trust_score: number
  explanation: string
}

export interface NetworkMapNode {
  id: string
  name: string
  device_type: string
  risk_level: RiskLevelAPI
  trust_score: number
  status: DeviceStatus
}

export interface NetworkMapEdge {
  source: string
  target: string
}

export interface NetworkMap {
  nodes: NetworkMapNode[]
  edges: NetworkMapEdge[]
}

export interface AlertOut {
  id: string
  device_id: string
  device_name: string
  alert_type: string
  severity: string
  message: string
  timestamp: string
}

export interface EventOut {
  id: string
  device_id: string
  event_type: string
  description: string
  timestamp: string
}

export interface SimulateAttackRequest {
  device_id: string
  attack_type?: AttackType
}

export interface SimulateAttackResponse {
  device_id: string
  attack_type: string
  old_trust_score: number
  new_trust_score: number
  old_risk_level: RiskLevelAPI
  new_risk_level: RiskLevelAPI
  alert_created: boolean
  message: string
}

export interface AddDeviceRequest {
  name: string
  device_type: string
  ip_address: string
  vendor: string
  trust_score?: number
  traffic_rate?: number
  status?: DeviceStatus
}
