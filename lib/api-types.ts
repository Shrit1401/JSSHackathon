export type RiskLevelAPI = "SAFE" | "LOW" | "MEDIUM" | "HIGH" | "COMPROMISED"

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
  stealth_level?: "low" | "medium" | "high"
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
  detection_difficulty?: number
}

export interface AddDeviceRequest {
  name: string
  device_type: string
  ip_address: string
  vendor: string
  trust_score?: number
  traffic_rate?: number
  status?: DeviceStatus
  parent_id?: string
}

export interface AddDeviceResponse {
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
  parent_id?: string
}

export interface ResetNetworkResponse {
  message: string
  devices_reset: number
}

export interface DeviceProfile {
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
  created_at: string
  profile: Record<string, unknown> | null
  baseline: Record<string, unknown> | null
  drift: Record<string, unknown> | null
  policy: Record<string, unknown> | null
  anomaly: Record<string, unknown> | null
  trust: Record<string, unknown> | null
  protection: Record<string, unknown> | null
  applicable_attacks: string[]
  security_explanation: string
}
