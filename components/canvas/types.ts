export type RiskLevel = "safe" | "suspicious" | "compromised"

export type NodeKind = "device" | "engine" | "alert" | "action"

export type DeviceNodeData = {
  kind: NodeKind
  name: string
  deviceType: string
  trustScore: number
  risk: RiskLevel
  isHub?: boolean
  muted?: boolean
  icon:
    | "router"
    | "camera"
    | "printer"
    | "laptop"
    | "tv"
    | "sensor"
    | "engine"
    | "alert"
    | "action"
  trustHistory: { t: number; v: number }[]
  trafficHistory: { t: number; v: number }[]
  lastEvent?: string
  pulseAt?: number
}

export type AlertItem = {
  id: string
  title: string
  description: string
  severity: RiskLevel
  createdAt: number
  nodeId?: string
  deviceName?: string
  confidence?: number
  indicators?: string[]
}

export type TrafficEdgeData = {
  status: "normal" | "suspicious" | "compromised" | "attack"
  speed?: number
  label?: string
}

