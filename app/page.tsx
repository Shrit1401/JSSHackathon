"use client"

import * as React from "react"
import ReactFlow, {
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
  type Node,
} from "reactflow"
import { AnimatePresence, motion } from "framer-motion"
import { Check, ChevronDown, Database, Plus, RotateCcw, Shield, Wifi, X } from "lucide-react"
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts"

import "reactflow/dist/style.css"
import dagre from "@dagrejs/dagre"

import { SecurityNode } from "@/components/canvas/SecurityNode"
import type {
  AlertItem,
  DeviceNodeData,
  RiskLevel,
  TrafficEdgeData,
} from "@/components/canvas/types"
import { TrafficEdge } from "@/components/canvas/TrafficEdge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type {
  RiskLevelAPI,
  DeviceSummary,
  NetworkMap,
  DeviceDetail as APIDeviceDetail,
} from "@/lib/api-types"

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n))
}

function riskFromTrust(trustScore: number): RiskLevel {
  if (trustScore >= 70) return "safe"
  if (trustScore >= 35) return "suspicious"
  return "compromised"
}

function badgeVariantForRisk(risk: RiskLevel) {
  if (risk === "safe") return "green"
  if (risk === "suspicious") return "orange"
  return "red"
}

function edgeStatusFromRisk(risk: RiskLevel): TrafficEdgeData["status"] {
  if (risk === "safe") return "normal"
  if (risk === "suspicious") return "suspicious"
  return "compromised"
}

function nowSeriesPoint(value: number) {
  return { t: Date.now(), v: Math.round(value) }
}

function seededSeries(seed: number, base: number, spread: number, count = 14) {
  const out: { t: number; v: number }[] = []
  let x = seed % 997
  const start = Date.now() - count * 60_000
  for (let i = 0; i < count; i++) {
    x = (x * 73 + 41) % 997
    const noise = (x / 997 - 0.5) * spread
    out.push({ t: start + i * 60_000, v: Math.round(base + noise) })
  }
  return out
}

function mkNodeData(
  kind: DeviceNodeData["kind"],
  name: string,
  deviceType: string,
  trustScore: number,
  icon: DeviceNodeData["icon"],
  seed: number
): DeviceNodeData {
  const risk = riskFromTrust(trustScore)
  return {
    kind,
    name,
    deviceType,
    trustScore,
    risk,
    icon,
    trustHistory: seededSeries(seed, trustScore, 16).map((p) => ({
      ...p,
      v: clamp(p.v, 0, 100),
    })),
    trafficHistory: seededSeries(seed + 11, 55, 36).map((p) => ({
      ...p,
      v: clamp(p.v, 0, 100),
    })),
  }
}

function mapRiskLevel(r: RiskLevelAPI): RiskLevel {
  if (r === "SAFE" || r === "LOW") return "safe"
  if (r === "MEDIUM") return "suspicious"
  if (r === "HIGH" || r === "COMPROMISED") return "compromised"
  return "compromised"
}

function mapIcon(deviceType: string): DeviceNodeData["icon"] {
  const t = deviceType.toLowerCase()
  if (t.includes("router") || t.includes("gateway")) return "router"
  if (t.includes("camera")) return "camera"
  if (t.includes("printer")) return "printer"
  if (t.includes("laptop") || t.includes("workstation")) return "laptop"
  if (t.includes("tv") || t.includes("media") || t.includes("display")) return "tv"
  if (
    t.includes("sensor") ||
    t.includes("iot") ||
    t.includes("thermostat") ||
    t.includes("lock")
  )
    return "sensor"
  return "sensor"
}

function hashCode(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0
  return Math.abs(h)
}

const HANDLE_NAMES = [
  "top-left",
  "left",
  "bottom-left",
  "bottom",
  "bottom-right",
  "right",
  "top-right",
]

type LayoutMode = "radial" | "vertical" | "horizontal"

const DAGRE_NODE_HEIGHT = 90

function computeSmartHandles(
  nodes: Node<DeviceNodeData>[],
  edges: Edge<TrafficEdgeData>[]
): Edge<TrafficEdgeData>[] {
  const posMap = new Map(nodes.map((n) => [n.id, n.position]))
  const hubIds = new Set(nodes.filter((n) => n.data.isHub).map((n) => n.id))

  return edges.map((edge) => {
    const sp = posMap.get(edge.source)
    const tp = posMap.get(edge.target)
    if (!sp || !tp) return edge

    const dx = tp.x - sp.x
    const dy = tp.y - sp.y

    let sourceHandle: string
    let targetHandle: string

    if (hubIds.has(edge.source)) {
      const angle = Math.atan2(dy, dx) * (180 / Math.PI)
      if (angle >= -22.5 && angle < 22.5) sourceHandle = "right"
      else if (angle >= 22.5 && angle < 67.5) sourceHandle = "bottom-right"
      else if (angle >= 67.5 && angle < 112.5) sourceHandle = "bottom"
      else if (angle >= 112.5 && angle < 157.5) sourceHandle = "bottom-left"
      else if (angle >= 157.5 || angle < -157.5) sourceHandle = "left"
      else if (angle >= -157.5 && angle < -112.5) sourceHandle = "top-left"
      else if (angle >= -112.5 && angle < -67.5) sourceHandle = "top"
      else sourceHandle = "top-right"
    } else {
      if (Math.abs(dx) >= Math.abs(dy)) {
        sourceHandle = dx >= 0 ? "source-right" : "source-left"
      } else {
        sourceHandle = dy >= 0 ? "source-bottom" : "source-top"
      }
    }

    if (Math.abs(dx) >= Math.abs(dy)) {
      targetHandle = dx >= 0 ? "target-left" : "target-right"
    } else {
      targetHandle = dy >= 0 ? "target-top" : "target-bottom"
    }

    return {
      ...edge,
      sourceHandle,
      targetHandle,
      data: edge.data
        ? { ...edge.data, pathType: undefined }
        : edge.data,
    }
  })
}

function applyDagreLayout(
  inputNodes: Node<DeviceNodeData>[],
  inputEdges: Edge<TrafficEdgeData>[],
  direction: "TB" | "LR"
): { nodes: Node<DeviceNodeData>[]; edges: Edge<TrafficEdgeData>[] } {
  const g = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: direction, nodesep: 80, ranksep: 140 })

  const nodeWidths = new Map<string, number>()
  inputNodes.forEach((node) => {
    const w = node.data.isHub ? 260 : 230
    nodeWidths.set(node.id, w)
    g.setNode(node.id, { width: w, height: DAGRE_NODE_HEIGHT })
  })

  inputEdges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  const nodes = inputNodes.map((node) => {
    const pos = g.node(node.id)
    const w = nodeWidths.get(node.id) ?? 230
    return {
      ...node,
      position: {
        x: pos.x - w / 2,
        y: pos.y - DAGRE_NODE_HEIGHT / 2,
      },
    }
  })

  const smartEdges = computeSmartHandles(nodes, inputEdges)
  const edges = smartEdges.map((edge) => ({
    ...edge,
    data: {
      ...(edge.data ?? { status: "normal" as const, speed: 2.5 }),
      pathType: "smoothstep" as const,
    },
  }))

  return { nodes, edges }
}

function applyRadialLayout(
  inputNodes: Node<DeviceNodeData>[],
  inputEdges: Edge<TrafficEdgeData>[]
): { nodes: Node<DeviceNodeData>[]; edges: Edge<TrafficEdgeData>[] } {
  const gatewayNode = inputNodes.find((n) => n.data.isHub)
  const gatewayId = gatewayNode?.id

  const childrenOf = new Map<string, string[]>()
  for (const edge of inputEdges) {
    if (!childrenOf.has(edge.source)) childrenOf.set(edge.source, [])
    childrenOf.get(edge.source)!.push(edge.target)
  }

  const positions = new Map<string, { x: number; y: number }>()
  if (gatewayId) {
    positions.set(gatewayId, { x: 0, y: 0 })
    const level1 = childrenOf.get(gatewayId) ?? []
    const radius = 420
    const angleStep = (2 * Math.PI) / Math.max(level1.length, 1)
    const startAngle = -Math.PI / 2
    level1.forEach((childId, i) => {
      const angle = startAngle + i * angleStep
      positions.set(childId, {
        x: Math.round(radius * Math.cos(angle)),
        y: Math.round(radius * Math.sin(angle)),
      })
      const level2 = childrenOf.get(childId) ?? []
      level2.forEach((gcId, j) => {
        const parentPos = positions.get(childId)!
        positions.set(gcId, {
          x: parentPos.x,
          y: parentPos.y + 140 * (j + 1),
        })
      })
    })
  }

  let fallbackX = -600
  inputNodes.forEach((n) => {
    if (!positions.has(n.id)) {
      positions.set(n.id, { x: fallbackX, y: 400 })
      fallbackX += 280
    }
  })

  const nodes = inputNodes.map((n) => ({
    ...n,
    position: positions.get(n.id) ?? n.position,
  }))

  const edges = computeSmartHandles(nodes, inputEdges)

  return { nodes, edges }
}

function buildFlowFromAPI(
  networkMap: NetworkMap,
  deviceLookup: Map<string, DeviceSummary>
): { nodes: Node<DeviceNodeData>[]; edges: Edge<TrafficEdgeData>[] } {
  const gatewayNode = networkMap.nodes.find(
    (n) =>
      n.device_type.toLowerCase().includes("router") ||
      n.device_type.toLowerCase().includes("gateway")
  )
  const gatewayId = gatewayNode?.id

  const childrenOf = new Map<string, string[]>()
  for (const edge of networkMap.edges) {
    if (!childrenOf.has(edge.source)) childrenOf.set(edge.source, [])
    childrenOf.get(edge.source)!.push(edge.target)
  }

  const positions = new Map<string, { x: number; y: number }>()
  if (gatewayId) {
    positions.set(gatewayId, { x: 0, y: 0 })
    const level1 = childrenOf.get(gatewayId) ?? []
    const radius = 420
    const angleStep = (2 * Math.PI) / Math.max(level1.length, 1)
    const startAngle = -Math.PI / 2
    level1.forEach((childId, i) => {
      const angle = startAngle + i * angleStep
      positions.set(childId, {
        x: Math.round(radius * Math.cos(angle)),
        y: Math.round(radius * Math.sin(angle)),
      })
      const level2 = childrenOf.get(childId) ?? []
      level2.forEach((gcId, j) => {
        const parentPos = positions.get(childId)!
        positions.set(gcId, {
          x: parentPos.x,
          y: parentPos.y + 140 * (j + 1),
        })
      })
    })
  }

  let fallbackX = -600
  networkMap.nodes.forEach((n) => {
    if (!positions.has(n.id)) {
      positions.set(n.id, { x: fallbackX, y: 400 })
      fallbackX += 280
    }
  })

  const flowNodes: Node<DeviceNodeData>[] = networkMap.nodes.map((apiNode) => {
    const device = deviceLookup.get(apiNode.id)
    const pos = positions.get(apiNode.id)!
    const isGateway = apiNode.id === gatewayId
    const risk = mapRiskLevel(apiNode.risk_level)
    const seed = hashCode(apiNode.id)
    return {
      id: apiNode.id,
      type: "security",
      position: pos,
      data: {
        kind: "device" as const,
        name: apiNode.name,
        deviceType: device?.device_type ?? apiNode.device_type,
        trustScore: apiNode.trust_score,
        risk,
        icon: mapIcon(apiNode.device_type),
        isHub: isGateway,
        trustHistory: seededSeries(seed, apiNode.trust_score, 16).map((p) => ({
          ...p,
          v: clamp(p.v, 0, 100),
        })),
        trafficHistory: seededSeries(
          seed + 11,
          device?.traffic_rate ?? 50,
          36
        ).map((p) => ({
          ...p,
          v: clamp(p.v, 0, 100),
        })),
      },
    }
  })

  const rawEdges: Edge<TrafficEdgeData>[] = networkMap.edges.map((apiEdge) => ({
    id: `e-${apiEdge.source}-${apiEdge.target}`,
    source: apiEdge.source,
    target: apiEdge.target,
    type: "traffic" as const,
    data: { status: "normal" as const, speed: 2.5 },
  }))

  return { nodes: flowNodes, edges: computeSmartHandles(flowNodes, rawEdges) }
}

function mapAlertFromAPI(a: {
  id: string
  device_id: string
  device_name: string
  alert_type: string
  severity: string
  message: string
  timestamp: string
}): AlertItem {
  const severityMap: Record<string, RiskLevel> = {
    CRITICAL: "compromised",
    HIGH: "compromised",
    MEDIUM: "suspicious",
    LOW: "safe",
    INFO: "safe",
  }
  return {
    id: a.id,
    title: a.alert_type.replace(/_/g, " "),
    description: a.message,
    severity: severityMap[a.severity.toUpperCase()] ?? "safe",
    createdAt: new Date(a.timestamp).getTime(),
    nodeId: a.device_id,
    deviceName: a.device_name,
  }
}

const initialNodes: Node<DeviceNodeData>[] = [
  // ─── Hub ────────────────────────────────────────────
  {
    id: "router",
    type: "security",
    position: { x: 0, y: 0 },
    data: { ...mkNodeData("device", "Router", "Gateway / NAT", 91, "router", 1), isHub: true },
  },

  // ─── Primary ring ──────────────────────────────────
  {
    id: "trust",
    type: "security",
    position: { x: -140, y: -280 },
    data: mkNodeData("engine", "Trust Engine", "Policy / Scoring", 93, "engine", 44),
  },
  {
    id: "cam21",
    type: "security",
    position: { x: -480, y: -140 },
    data: mkNodeData("device", "Camera_21", "Security Camera", 82, "camera", 21),
  },
  {
    id: "laptop1",
    type: "security",
    position: { x: 360, y: -300 },
    data: {
      ...mkNodeData("device", "Laptop_1", "Workstation", 76, "laptop", 31),
      lastEvent: "Persistence / Backdoor",
    },
  },
  {
    id: "alerts",
    type: "security",
    position: { x: 480, y: -80 },
    data: mkNodeData("engine", "Alert System", "Detections", 88, "alert", 18),
  },
  {
    id: "printer3",
    type: "security",
    position: { x: 420, y: 220 },
    data: mkNodeData("device", "Printer_3", "Network Printer", 69, "printer", 13),
  },
  {
    id: "sensor",
    type: "security",
    position: { x: -60, y: 300 },
    data: mkNodeData("device", "IoT_Sensor", "Env Sensor", 74, "sensor", 9),
  },
  {
    id: "tv",
    type: "security",
    position: { x: -480, y: 180 },
    data: mkNodeData("device", "SmartTV", "Media Device", 61, "tv", 7),
  },

  // ─── Child devices ─────────────────────────────────
  // SmartTV children (below, stacked vertically like IoT)
  {
    id: "projector",
    type: "security",
    position: { x: -480, y: 320 },
    data: mkNodeData("device", "Projector", "Display Device", 58, "tv", 50),
  },
  {
    id: "soundbar",
    type: "security",
    position: { x: -480, y: 460 },
    data: mkNodeData("device", "Soundbar", "Audio Device", 64, "sensor", 51),
  },

  // Camera_21 children (below, stacked vertically like IoT)
  {
    id: "cam22",
    type: "security",
    position: { x: -480, y: 0 },
    data: mkNodeData("device", "Camera_22", "Security Camera", 80, "camera", 22),
  },
  {
    id: "nvr",
    type: "security",
    position: { x: -480, y: 140 },
    data: mkNodeData("device", "NVR_1", "Video Recorder", 78, "camera", 55),
  },

  // Laptop_1 children (to the right, stacked vertically)
  {
    id: "phone1",
    type: "security",
    position: { x: 640, y: -360 },
    data: mkNodeData("device", "Phone_1", "Mobile Device", 72, "laptop", 60),
  },
  {
    id: "tablet1",
    type: "security",
    position: { x: 640, y: -220 },
    data: mkNodeData("device", "Tablet_1", "Mobile Device", 74, "laptop", 61),
  },

  // Printer_3 children (to the right, stacked vertically)
  {
    id: "scanner1",
    type: "security",
    position: { x: 700, y: 160 },
    data: mkNodeData("device", "Scanner_1", "Document Scanner", 66, "printer", 70),
  },
  {
    id: "fax1",
    type: "security",
    position: { x: 700, y: 300 },
    data: mkNodeData("device", "Fax_1", "Fax Machine", 62, "printer", 71),
  },

  // IoT_Sensor children (below, stacked vertically)
  {
    id: "thermostat",
    type: "security",
    position: { x: -60, y: 440 },
    data: mkNodeData("device", "Thermostat", "HVAC Control", 70, "sensor", 80),
  },
  {
    id: "doorlock",
    type: "security",
    position: { x: -60, y: 580 },
    data: mkNodeData("device", "DoorLock_1", "Smart Lock", 68, "sensor", 81),
  },
]

const initialEdges: Edge<TrafficEdgeData>[] = [
  { id: "e-router-trust", source: "router", sourceHandle: "top-left", target: "trust", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.8 } },
  { id: "e-router-cam", source: "router", sourceHandle: "left", target: "cam21", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.6 } },
  { id: "e-router-laptop", source: "router", sourceHandle: "top-right", target: "laptop1", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.2 } },
  { id: "e-router-alerts", source: "router", sourceHandle: "right", target: "alerts", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 4.2 } },
  { id: "e-router-printer", source: "router", sourceHandle: "bottom-right", target: "printer3", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.8 } },
  { id: "e-router-sensor", source: "router", sourceHandle: "bottom", target: "sensor", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.4 } },
  { id: "e-router-tv", source: "router", sourceHandle: "bottom-left", target: "tv", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.2 } },
  { id: "e-tv-projector", source: "tv", sourceHandle: "source-right", target: "projector", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.0 } },
  { id: "e-tv-soundbar", source: "tv", sourceHandle: "source-right", target: "soundbar", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.0 } },
  { id: "e-cam-cam22", source: "cam21", sourceHandle: "source-right", target: "cam22", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.8 } },
  { id: "e-cam-nvr", source: "cam21", sourceHandle: "source-right", target: "nvr", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.8 } },
  { id: "e-laptop-phone", source: "laptop1", sourceHandle: "source-right", target: "phone1", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.4 } },
  { id: "e-laptop-tablet", source: "laptop1", sourceHandle: "source-right", target: "tablet1", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.4 } },
  { id: "e-printer-scanner", source: "printer3", sourceHandle: "source-right", target: "scanner1", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.2 } },
  { id: "e-printer-fax", source: "printer3", sourceHandle: "source-right", target: "fax1", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 3.2 } },
  { id: "e-sensor-thermo", source: "sensor", sourceHandle: "source-right", target: "thermostat", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.6 } },
  { id: "e-sensor-door", source: "sensor", sourceHandle: "source-right", target: "doorlock", targetHandle: "target-left", type: "traffic", data: { status: "normal", speed: 2.6 } },
]

function computeTrustScore(nodes: Node<DeviceNodeData>[]) {
  const deviceNodes = nodes.filter((n) => n.data.kind === "device")
  const avg =
    deviceNodes.reduce((acc, n) => acc + n.data.trustScore, 0) /
    Math.max(1, deviceNodes.length)
  return Math.round(avg)
}

function computeStats(nodes: Node<DeviceNodeData>[]) {
  const deviceNodes = nodes.filter((n) => n.data.kind === "device")
  const total = deviceNodes.length
  const safe = deviceNodes.filter((n) => n.data.risk === "safe").length
  const suspicious = deviceNodes.filter((n) => n.data.risk === "suspicious").length
  const compromised = deviceNodes.filter((n) => n.data.risk === "compromised").length
  return { total, safe, suspicious, compromised }
}

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`
}

type SimulationType = "backdoor" | "traffic_spike" | "exfil" | "malware"

interface DeviceOption {
  id: string
  name: string
}

interface MockDevicePayload {
  name: string
  deviceType: string
  parentId: string
}

function AddDeviceModal({
  open,
  useMock,
  existingDevices,
  onClose,
  onAdded,
}: {
  open: boolean
  useMock: boolean
  existingDevices: DeviceOption[]
  onClose: () => void
  onAdded: (mockDevice?: MockDevicePayload) => void
}) {
  const [name, setName] = React.useState("")
  const [deviceType, setDeviceType] = React.useState("sensor")
  const [ip, setIp] = React.useState("")
  const [vendor, setVendor] = React.useState("")
  const [parentId, setParentId] = React.useState("")
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  function reset() {
    setName("")
    setDeviceType("sensor")
    setIp("")
    setVendor("")
    setParentId("")
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !ip.trim() || !vendor.trim()) {
      setError("Name, IP and vendor are required.")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      if (useMock) {
        const payload: MockDevicePayload = {
          name: name.trim(),
          deviceType,
          parentId: parentId || "router",
        }
        reset()
        onAdded(payload)
        onClose()
      } else {
        await api.addDevice({
          name: name.trim(),
          device_type: deviceType,
          ip_address: ip.trim(),
          vendor: vendor.trim(),
          ...(parentId ? { parent_id: parentId } : {}),
        })
        reset()
        onAdded()
        onClose()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add device")
    } finally {
      setSubmitting(false)
    }
  }

  const DEVICE_TYPES = [
    "sensor",
    "camera",
    "printer",
    "laptop",
    "smart_tv",
    "router",
    "thermostat",
    "hub",
  ]

  const inputCn =
    "w-full rounded-lg border border-white/10 bg-zinc-900/40 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 outline-none focus:border-cyan-400/40 focus:ring-1 focus:ring-cyan-400/20"

  return (
    <AnimatePresence initial={false}>
      {open ? (
        <motion.div
          key="add-device-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            onClick={(e) => e.stopPropagation()}
            className="w-[400px] rounded-2xl border border-white/10 bg-zinc-950/90 p-6 shadow-[0_24px_80px_rgba(0,0,0,0.8)] backdrop-blur-md"
            style={{
              fontFamily:
                '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
            }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-50">
                Add device
              </h2>
              <button
                onClick={onClose}
                className="rounded-lg p-1 text-zinc-400 transition-colors hover:bg-white/5 hover:text-zinc-100"
              >
                <X className="size-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div>
                <label className="mb-1 block text-xs text-zinc-400">
                  Name
                </label>
                <input
                  className={inputCn}
                  placeholder="Living Room Camera"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div>
                <label className="mb-1 block text-xs text-zinc-400">
                  Device type
                </label>
                <select
                  className={inputCn + " appearance-none"}
                  value={deviceType}
                  onChange={(e) => setDeviceType(e.target.value)}
                >
                  {DEVICE_TYPES.map((t) => (
                    <option key={t} value={t} className="bg-zinc-900">
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs text-zinc-400">
                  Parent device
                </label>
                <select
                  className={inputCn + " appearance-none"}
                  value={parentId}
                  onChange={(e) => setParentId(e.target.value)}
                >
                  <option value="" className="bg-zinc-900">Auto (based on type)</option>
                  {existingDevices.map((d) => (
                    <option key={d.id} value={d.id} className="bg-zinc-900">
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs text-zinc-400">
                    IP address
                  </label>
                  <input
                    className={inputCn}
                    placeholder="192.168.1.50"
                    value={ip}
                    onChange={(e) => setIp(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-zinc-400">
                    Vendor
                  </label>
                  <input
                    className={inputCn}
                    placeholder="Acme"
                    value={vendor}
                    onChange={(e) => setVendor(e.target.value)}
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                  {error}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="text-zinc-300 hover:bg-white/5"
                  onClick={onClose}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={submitting}
                  className="bg-cyan-500/90 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
                >
                  {submitting ? "Adding…" : "Add device"}
                </Button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

type StealthLevel = "low" | "medium" | "high"

function TopToolbar({
  trustScore,
  alerts,
  devices,
  useMock,
  onToggleMock,
  onAddDevice,
  onSimulate,
  onResetNetwork,
  resetting,
}: {
  trustScore: number
  alerts: AlertItem[]
  devices: DeviceOption[]
  useMock: boolean
  onToggleMock: () => void
  onAddDevice: () => void
  onSimulate: (type: SimulationType, deviceId: string, stealthLevel?: StealthLevel) => void
  onResetNetwork: () => void
  resetting: boolean
}) {
  const trustRisk = riskFromTrust(trustScore)
  const [open, setOpen] = React.useState(false)
  const [deviceOpen, setDeviceOpen] = React.useState(false)
  const [selectedDevice, setSelectedDevice] = React.useState<string | null>(null)
  const [stealthLevel, setStealthLevel] = React.useState<StealthLevel>("medium")
  const [stealthOpen, setStealthOpen] = React.useState(false)

  const selectedName =
    devices.find((d) => d.id === selectedDevice)?.name ?? "Select device"

  function fire(type: SimulationType) {
    if (!selectedDevice) return
    setOpen(false)
    onSimulate(type, selectedDevice, type === "backdoor" ? stealthLevel : undefined)
  }

  return (
    <div
      className="pointer-events-none absolute inset-x-0 top-4 z-30 flex justify-start px-5"
      style={{
        fontFamily:
          '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
      }}
    >
      <div className="pointer-events-auto flex items-center gap-6 rounded-2xl border border-white/10 bg-zinc-950/40 px-6 py-4 shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl border border-white/10 bg-zinc-900/50">
            <Shield className="size-5 text-cyan-200" />
          </div>
          <div className="text-base font-semibold tracking-tight text-zinc-50">
            Cyber Canvas
          </div>
        </div>

        <div className="flex items-center gap-6 text-[15px]">
          <div className="flex items-baseline gap-1.5">
            <span className="text-zinc-400">Risk</span>
            <span className="font-semibold tabular-nums text-zinc-100">
              {100 - trustScore}%
            </span>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-900/30 px-2.5 py-1.5">
            <span className="text-zinc-400">Trust</span>
            <span className="font-semibold tabular-nums text-zinc-100">
              {trustScore}%
            </span>
            <Badge
              variant={badgeVariantForRisk(trustRisk)}
              className="capitalize"
            >
              {trustRisk}
            </Badge>
          </div>

          <div className="text-zinc-400">
            Alerts{" "}
            <span className="font-semibold text-zinc-100 tabular-nums">
              {alerts.length}
            </span>
          </div>

          {/* ── Device selector ── */}
          <div className="relative">
            <Button
              size="sm"
              variant="outline"
              className="border-white/10 bg-zinc-950/25 text-zinc-100 hover:bg-zinc-900/50"
              onClick={() => {
                setDeviceOpen((v) => !v)
                setOpen(false)
              }}
            >
              <span className="max-w-[120px] truncate">{selectedName}</span>
              <ChevronDown className="ml-1.5 size-3.5 text-zinc-300" />
            </Button>
            <AnimatePresence initial={false}>
              {deviceOpen ? (
                <motion.div
                  initial={{ opacity: 0, y: -6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -6, scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  className="absolute left-0 top-[calc(100%+6px)] max-h-60 w-52 overflow-y-auto rounded-xl border border-white/10 bg-zinc-950/80 p-1 shadow-[0_16px_50px_rgba(0,0,0,0.65)] backdrop-blur-md"
                  style={{
                    fontFamily:
                      '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
                  }}
                >
                  {devices.map((d) => (
                    <button
                      key={d.id}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm text-zinc-100 transition-colors hover:bg-white/5",
                        selectedDevice === d.id && "bg-white/5"
                      )}
                      onClick={() => {
                        setSelectedDevice(d.id)
                        setDeviceOpen(false)
                      }}
                    >
                      {selectedDevice === d.id && (
                        <Check className="size-3.5 text-cyan-300" />
                      )}
                      <span className="truncate">{d.name}</span>
                    </button>
                  ))}
                  {devices.length === 0 && (
                    <div className="px-3 py-2 text-xs text-zinc-500">
                      No devices
                    </div>
                  )}
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>

          {/* ── Attack type selector ── */}
          <div className="relative">
            <Button
              size="sm"
              variant="outline"
              className={cn(
                "border-white/10 bg-zinc-950/25 text-zinc-100 hover:bg-zinc-900/50",
                !selectedDevice && "opacity-50"
              )}
              disabled={!selectedDevice}
              onClick={() => {
                setOpen((v) => !v)
                setDeviceOpen(false)
              }}
            >
              Simulate
              <ChevronDown className="ml-1.5 size-3.5 text-zinc-300" />
            </Button>
            <AnimatePresence initial={false}>
              {open ? (
                <motion.div
                  initial={{ opacity: 0, y: -6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -6, scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  className="absolute right-0 top-[calc(100%+6px)] w-44 rounded-xl border border-white/10 bg-zinc-950/80 p-1 shadow-[0_16px_50px_rgba(0,0,0,0.65)] backdrop-blur-md"
                  style={{
                    fontFamily:
                      '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
                  }}
                >
                  <Button
                    size="sm"
                    variant="ghost"
                    className="w-full justify-start text-zinc-100 hover:bg-white/5"
                    onClick={() => fire("backdoor")}
                  >
                    Backdoor
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="w-full justify-start text-zinc-100 hover:bg-white/5"
                    onClick={() => fire("traffic_spike")}
                  >
                    Traffic spike
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="w-full justify-start text-zinc-100 hover:bg-white/5"
                    onClick={() => fire("exfil")}
                  >
                    Data exfiltration
                  </Button>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>

          {/* ── Stealth level ── */}
          <div className="relative">
            <Button
              size="sm"
              variant="outline"
              className={cn(
                "border-white/10 bg-zinc-950/25 text-zinc-100 hover:bg-zinc-900/50",
                !selectedDevice && "opacity-50"
              )}
              disabled={!selectedDevice}
              onClick={() => {
                setStealthOpen((v) => !v)
                setOpen(false)
                setDeviceOpen(false)
              }}
            >
              <span className="capitalize">Stealth: {stealthLevel}</span>
              <ChevronDown className="ml-1.5 size-3.5 text-zinc-300" />
            </Button>
            <AnimatePresence initial={false}>
              {stealthOpen ? (
                <motion.div
                  initial={{ opacity: 0, y: -6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -6, scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  className="absolute right-0 top-[calc(100%+6px)] w-36 rounded-xl border border-white/10 bg-zinc-950/80 p-1 shadow-[0_16px_50px_rgba(0,0,0,0.65)] backdrop-blur-md"
                  style={{
                    fontFamily:
                      '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
                  }}
                >
                  {(["low", "medium", "high"] as StealthLevel[]).map((level) => (
                    <button
                      key={level}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm text-zinc-100 transition-colors hover:bg-white/5",
                        stealthLevel === level && "bg-white/5"
                      )}
                      onClick={() => {
                        setStealthLevel(level)
                        setStealthOpen(false)
                      }}
                    >
                      {stealthLevel === level && (
                        <Check className="size-3.5 text-cyan-300" />
                      )}
                      <span className="capitalize">{level}</span>
                      <span className="ml-auto text-[10px] text-zinc-500">
                        {level === "low" ? "Easy detect" : level === "medium" ? "Moderate" : "Hard detect"}
                      </span>
                    </button>
                  ))}
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>

          {/* ── Add device ── */}
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 bg-zinc-950/25 text-zinc-100 hover:bg-zinc-900/50"
            onClick={onAddDevice}
          >
            <Plus className="mr-1 size-3.5" />
            Add
          </Button>

          {/* ── Reset network ── */}
          <Button
            size="sm"
            variant="outline"
            className="border-white/10 bg-zinc-950/25 text-zinc-100 hover:bg-zinc-900/50 disabled:opacity-50"
            disabled={resetting}
            onClick={onResetNetwork}
          >
            <RotateCcw className={cn("mr-1 size-3.5", resetting && "animate-spin")} />
            {resetting ? "Resetting…" : "Reset"}
          </Button>

          {/* ── Mock / Live toggle ── */}
          <button
            onClick={onToggleMock}
            className={cn(
              "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors",
              useMock
                ? "border-orange-400/30 bg-orange-500/10 text-orange-300"
                : "border-cyan-400/30 bg-cyan-500/10 text-cyan-300"
            )}
          >
            {useMock ? (
              <Database className="size-3.5" />
            ) : (
              <Wifi className="size-3.5" />
            )}
            {useMock ? "Mock" : "Live"}
          </button>
        </div>
      </div>
    </div>
  )
}

function DetailPanel({
  node,
  alerts,
  deviceDetail,
  onClose,
}: {
  node: Node<DeviceNodeData> | null
  alerts: AlertItem[]
  deviceDetail: APIDeviceDetail | null
  onClose: () => void
}) {
  return (
    <AnimatePresence initial={false}>
      {node ? (
        <motion.div
          key={node.id}
          initial={{ x: 18, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 22, opacity: 0 }}
          transition={{ type: "spring", stiffness: 360, damping: 34 }}
          className="absolute right-4 top-16 bottom-4 z-30 w-[380px] max-w-[calc(100vw-2rem)]"
        >
          <Card className="flex h-full flex-col overflow-hidden border-white/10 bg-zinc-950/65 text-zinc-50 shadow-[0_20px_70px_rgba(0,0,0,0.7)] backdrop-blur-md" style={{ fontFamily: '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif' }}>
            <CardHeader className="shrink-0 pb-2">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="truncate">{node.data.name}</CardTitle>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <div className="text-xs text-zinc-400">
                      {node.data.deviceType}
                    </div>
                    <Badge
                      variant={badgeVariantForRisk(node.data.risk)}
                      className="capitalize"
                    >
                      {node.data.risk}
                    </Badge>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-zinc-200 hover:bg-white/5"
                  onClick={onClose}
                >
                  Close
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 space-y-4 overflow-y-auto">
              {alerts.length > 0 && (
                (() => {
                  const match =
                    alerts.find(
                      (a) =>
                        a.nodeId === node.id ||
                        a.deviceName === node.data.name
                    ) ?? alerts[0]
                  if (!match) return null
                  return (
                    <div className="rounded-2xl border border-red-400/45 bg-zinc-950/80 p-3 text-[11px] shadow-[0_16px_50px_rgba(0,0,0,0.8)]">
                      <div className="text-[11px] font-semibold tracking-[0.2em] text-red-300">
                        {match.title.toUpperCase()}
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div>
                          <div className="text-zinc-500">Device</div>
                          <div className="mt-0.5 text-sm font-semibold text-zinc-100">
                            {match.deviceName ?? node.data.name}
                          </div>
                        </div>
                        <div>
                          <div className="text-zinc-500">Severity</div>
                          <div className="mt-0.5 text-sm font-semibold text-red-300">
                            {match.severity === "compromised"
                              ? "CRITICAL"
                              : match.severity === "suspicious"
                                ? "HIGH"
                                : "INFO"}
                          </div>
                        </div>
                        <div>
                          <div className="text-zinc-500">Confidence</div>
                          <div className="mt-0.5 text-sm font-semibold text-zinc-100">
                            {match.confidence ?? 92}%
                          </div>
                        </div>
                        <div>
                          <div className="text-zinc-500">Active alerts</div>
                          <div className="mt-0.5 text-sm font-semibold text-zinc-100">
                            {alerts.length}
                          </div>
                        </div>
                        {match.detectionDifficulty != null && (
                          <div>
                            <div className="text-zinc-500">Detection difficulty</div>
                            <div className={cn(
                              "mt-0.5 text-sm font-semibold",
                              match.detectionDifficulty >= 70 ? "text-emerald-300" : match.detectionDifficulty >= 40 ? "text-orange-300" : "text-red-300"
                            )}>
                              {match.detectionDifficulty}%
                              <span className="ml-1 text-[10px] font-normal text-zinc-500">
                                {match.detectionDifficulty >= 70 ? "Easy" : match.detectionDifficulty >= 40 ? "Moderate" : "Hard"}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="mt-3 text-[11px] text-zinc-500">
                        Indicators
                      </div>
                      <ul className="mt-1 space-y-1 text-[11px] text-zinc-200">
                        {(match.indicators ??
                          [
                            "Persistence registry key",
                            "Beaconing traffic",
                            "Suspicious outbound IP",
                          ]).map((ind) => (
                          <li
                            key={ind}
                            className="flex items-start gap-1.5"
                          >
                            <span className="mt-[3px] h-1.5 w-1.5 rounded-full bg-red-300" />
                            <span>{ind}</span>
                          </li>
                        ))}
                      </ul>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          className="bg-red-500/90 text-xs font-medium text-white hover:bg-red-500"
                        >
                          Isolate Device
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/20 bg-zinc-900/40 text-xs text-zinc-100 hover:bg-zinc-900/70"
                        >
                          Block IP
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/10 bg-zinc-900/40 text-xs text-zinc-100 hover:bg-zinc-900/70"
                        >
                          Investigate
                        </Button>
                      </div>
                    </div>
                  )
                })()
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-white/10 bg-zinc-900/30 p-3">
                  <div className="text-[11px] text-zinc-500">Trust score</div>
                  <div className="mt-1 text-2xl font-semibold tabular-nums">
                    {Math.round(node.data.trustScore)}%
                  </div>
                  <div className="mt-1 text-[11px] text-zinc-500">
                    Updated on simulation events
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-zinc-900/30 p-3">
                  <div className="text-[11px] text-zinc-500">Last event</div>
                  <div className="mt-1 text-sm text-zinc-200">
                    {node.data.lastEvent ?? "No recent anomalies"}
                  </div>
                  <div className="mt-1 text-[11px] text-zinc-500">
                    Telemetry + detections
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                <div className="text-xs font-medium text-zinc-200">
                  Trust history
                </div>
                <div className="mt-2 h-28 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={node.data.trustHistory.map((p) => ({
                        time: p.t,
                        trust: p.v,
                      }))}
                      margin={{ left: -18, right: 6, top: 6, bottom: 0 }}
                    >
                      <XAxis hide dataKey="time" />
                      <YAxis hide domain={[0, 100]} />
                      <RechartsTooltip
                        contentStyle={{
                          background: "rgba(9, 9, 11, 0.92)",
                          border: "1px solid rgba(255,255,255,0.08)",
                          borderRadius: 12,
                        }}
                        labelFormatter={() => ""}
                        formatter={(v) => [`${v}%`, "Trust"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="trust"
                        stroke="rgba(34,211,238,0.9)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                <div className="text-xs font-medium text-zinc-200">
                  Traffic history
                </div>
                <div className="mt-2 h-28 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={node.data.trafficHistory.map((p) => ({
                        time: p.t,
                        traffic: p.v,
                      }))}
                      margin={{ left: -18, right: 6, top: 6, bottom: 0 }}
                    >
                      <XAxis hide dataKey="time" />
                      <YAxis hide domain={[0, 100]} />
                      <RechartsTooltip
                        contentStyle={{
                          background: "rgba(9, 9, 11, 0.92)",
                          border: "1px solid rgba(255,255,255,0.08)",
                          borderRadius: 12,
                        }}
                        labelFormatter={() => ""}
                        formatter={(v) => [`${v}`, "Traffic"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="traffic"
                        stroke="rgba(161,161,170,0.65)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {deviceDetail && deviceDetail.open_ports.length > 0 && (
                <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                  <div className="text-xs font-medium text-zinc-200">
                    Open ports
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {deviceDetail.open_ports.map((port) => (
                      <span
                        key={port}
                        className="rounded-md border border-white/10 bg-zinc-900/40 px-2 py-0.5 text-[11px] tabular-nums text-zinc-300"
                      >
                        {port}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {deviceDetail &&
                Object.keys(deviceDetail.protocol_usage).length > 0 && (
                  <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                    <div className="text-xs font-medium text-zinc-200">
                      Protocol usage
                    </div>
                    <div className="mt-1.5 space-y-1.5">
                      {Object.entries(deviceDetail.protocol_usage).map(
                        ([proto, pct]) => (
                          <div key={proto} className="flex items-center gap-2">
                            <span className="w-14 text-[11px] text-zinc-400">
                              {proto}
                            </span>
                            <div className="h-1.5 flex-1 rounded-full bg-zinc-800">
                              <div
                                className="h-1.5 rounded-full bg-cyan-400/50"
                                style={{
                                  width: `${Math.round(pct * 100)}%`,
                                }}
                              />
                            </div>
                            <span className="w-10 text-right text-[11px] tabular-nums text-zinc-300">
                              {Math.round(pct * 100)}%
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

              <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                <div className="text-xs font-medium text-zinc-200">
                  Security explanation
                </div>
                <div className="mt-1 text-[12px] leading-5 text-zinc-400">
                  {deviceDetail?.security_explanation ??
                    "Trust is derived from behavior, policy compliance, and anomaly detection. Simulations inject suspicious patterns; connections and risk indicators update immediately on the canvas."}
                </div>
              </div>

              {deviceDetail && (
                <div className="rounded-xl border border-white/10 bg-zinc-900/20 p-3">
                  <div className="text-xs font-medium text-zinc-200">
                    Device info
                  </div>
                  <div className="mt-1.5 grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-zinc-500">IP</span>
                      <div className="mt-0.5 tabular-nums text-zinc-200">
                        {deviceDetail.ip_address}
                      </div>
                    </div>
                    <div>
                      <span className="text-zinc-500">Vendor</span>
                      <div className="mt-0.5 text-zinc-200">
                        {deviceDetail.vendor}
                      </div>
                    </div>
                    <div>
                      <span className="text-zinc-500">Status</span>
                      <div className="mt-0.5 text-zinc-200 capitalize">
                        {deviceDetail.status}
                      </div>
                    </div>
                    <div>
                      <span className="text-zinc-500">Traffic</span>
                      <div className="mt-0.5 tabular-nums text-zinc-200">
                        {deviceDetail.traffic_rate.toFixed(1)} MB/s
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}

function SkeletonNode({
  className,
  style,
}: {
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-zinc-950/55 p-3.5 shadow-[0_10px_30px_rgba(0,0,0,0.45)] backdrop-blur-md",
        className
      )}
      style={style}
    >
      <div className="flex items-start gap-2.5">
        <Skeleton className="size-8 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="size-8 rounded-full" />
      </div>
      <div className="mt-3 flex items-center justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-5 w-14 rounded-full" />
      </div>
    </div>
  )
}

function CanvasSkeleton() {
  return (
    <div
      className="absolute inset-0 flex items-center justify-center"
      style={{
        fontFamily:
          '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif',
      }}
    >
      {/* Top toolbar skeleton */}
      <div className="absolute inset-x-0 top-4 z-30 flex justify-start px-5">
        <div className="flex items-center gap-7 rounded-2xl border border-white/10 bg-zinc-950/40 px-6 py-4 shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Skeleton className="size-10 rounded-xl" />
            <Skeleton className="h-5 w-28" />
          </div>
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-7 w-24 rounded-xl" />
          <Skeleton className="h-4 w-14" />
          <Skeleton className="h-8 w-24 rounded-lg" />
        </div>
      </div>

      {/* Central hub skeleton */}
      <SkeletonNode className="absolute w-[260px]" />

      {/* Orbiting node skeletons */}
      {[
        { x: -420, y: -140 },
        { x: -140, y: -280 },
        { x: 280, y: -260 },
        { x: 400, y: -40 },
        { x: 340, y: 200 },
        { x: -60, y: 280 },
        { x: -420, y: 160 },
      ].map((pos, i) => (
        <SkeletonNode
          key={i}
          className="absolute w-[230px]"
          style={
            {
              transform: `translate(${pos.x}px, ${pos.y}px)`,
              animationDelay: `${i * 150}ms`,
            } as React.CSSProperties
          }
        />
      ))}

      {/* Connector line skeletons */}
      <svg className="pointer-events-none absolute inset-0 size-full">
        {[
          { x1: "50%", y1: "50%", x2: "28%", y2: "36%" },
          { x1: "50%", y1: "50%", x2: "42%", y2: "26%" },
          { x1: "50%", y1: "50%", x2: "63%", y2: "28%" },
          { x1: "50%", y1: "50%", x2: "68%", y2: "46%" },
          { x1: "50%", y1: "50%", x2: "64%", y2: "65%" },
          { x1: "50%", y1: "50%", x2: "46%", y2: "70%" },
          { x1: "50%", y1: "50%", x2: "28%", y2: "60%" },
        ].map((l, i) => (
          <line
            key={i}
            {...l}
            stroke="rgba(34,211,238,0.08)"
            strokeWidth="2"
            className="animate-pulse"
            style={{ animationDelay: `${i * 200}ms` }}
          />
        ))}
      </svg>

      {/* Bottom-left breakdown skeleton */}
      <div className="absolute left-4 bottom-4 z-30">
        <div className="rounded-2xl border border-white/10 bg-zinc-950/60 px-5 py-3.5 shadow-[0_14px_45px_rgba(0,0,0,0.7)] backdrop-blur-md">
          <Skeleton className="h-3 w-32" />
          <div className="mt-2.5 grid grid-cols-2 gap-x-6 gap-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-22" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      </div>

      {/* Loading indicator */}
      <div className="absolute bottom-4 right-4 z-30 flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-950/60 px-4 py-2 backdrop-blur-md">
        <div className="size-2 animate-pulse rounded-full bg-cyan-400" />
        <span className="text-xs text-zinc-400">Loading network map…</span>
      </div>
    </div>
  )
}

function CanvasInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const [selectedId, setSelectedId] = React.useState<string | null>(null)
  const [alerts, setAlerts] = React.useState<AlertItem[]>([])
  const [pulse, setPulse] = React.useState<Record<string, number>>({})
  const [deviceDetail, setDeviceDetail] = React.useState<APIDeviceDetail | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [useMock, setUseMock] = React.useState(false)
  const [addDeviceOpen, setAddDeviceOpen] = React.useState(false)
  const [resetting, setResetting] = React.useState(false)
  const [layoutMode, setLayoutMode] = React.useState<LayoutMode>("radial")

  const { fitView } = useReactFlow()
  const nodesRef = React.useRef(nodes)
  const edgesRef = React.useRef(edges)
  nodesRef.current = nodes
  edgesRef.current = edges

  const loadFromAPI = React.useCallback(async () => {
    try {
      const [networkMap, devices, apiAlerts] = await Promise.all([
        api.networkMap(),
        api.devices(),
        api.alerts(),
      ])
      const deviceLookup = new Map(devices.map((d) => [d.id, d]))
      const { nodes: flowNodes, edges: flowEdges } = buildFlowFromAPI(
        networkMap,
        deviceLookup
      )
      setNodes(flowNodes)
      setEdges(flowEdges)
      setAlerts(apiAlerts.map(mapAlertFromAPI))
      return true
    } catch (err) {
      console.error("API load failed:", err)
      return false
    }
  }, [setNodes, setEdges])

  const loadMock = React.useCallback(() => {
    setNodes(initialNodes)
    setEdges(computeSmartHandles(initialNodes, initialEdges))
    setAlerts([])
  }, [setNodes, setEdges])

  const addMockDevice = React.useCallback(
    (payload: MockDevicePayload) => {
      const id = uid("device")
      const seed = hashCode(id)
      const icon = mapIcon(payload.deviceType)
      const trustScore = 60 + Math.floor(Math.random() * 30)
      const newNode: Node<DeviceNodeData> = {
        id,
        type: "security",
        position: { x: 0, y: 0 },
        data: mkNodeData("device", payload.name, payload.deviceType, trustScore, icon, seed),
      }
      const newEdge: Edge<TrafficEdgeData> = {
        id: `e-${payload.parentId}-${id}`,
        source: payload.parentId,
        target: id,
        type: "traffic",
        data: { status: "normal", speed: 2.5 },
      }
      setNodes((prev) => {
        const next = [...prev, newNode]
        const allEdges = [...edgesRef.current, newEdge]
        const laid = applyRadialLayout(next, allEdges)
        setEdges(laid.edges)
        setTimeout(() => fitView({ padding: 0.22, duration: 300 }), 50)
        return laid.nodes
      })
    },
    [setNodes, setEdges, fitView]
  )

  const refreshCanvas = React.useCallback(
    async (mockDevice?: MockDevicePayload) => {
      if (mockDevice) {
        addMockDevice(mockDevice)
        return
      }
      if (useMock) {
        loadMock()
      } else {
        await loadFromAPI()
      }
    },
    [useMock, loadFromAPI, loadMock, addMockDevice]
  )

  React.useEffect(() => {
    let cancelled = false
    async function init() {
      if (useMock) {
        loadMock()
      } else {
        const ok = await loadFromAPI()
        if (!ok && !cancelled) loadMock()
      }
      if (!cancelled) setLoading(false)
    }
    init()
    return () => {
      cancelled = true
    }
  }, [useMock, loadFromAPI, loadMock])

  const trustScore = React.useMemo(() => computeTrustScore(nodes), [nodes])
  const stats = React.useMemo(() => computeStats(nodes), [nodes])
  const selectedNode = React.useMemo(
    () => nodes.find((n) => n.id === selectedId) ?? null,
    [nodes, selectedId]
  )
  const hasCompromised = React.useMemo(
    () => nodes.some((n) => n.data.risk === "compromised"),
    [nodes]
  )

  React.useEffect(() => {
    if (!selectedId || useMock) {
      setDeviceDetail(null)
      return
    }
    let cancelled = false
    api
      .device(selectedId)
      .then((detail) => {
        if (!cancelled) setDeviceDetail(detail)
      })
      .catch(() => setDeviceDetail(null))
    return () => {
      cancelled = true
    }
  }, [selectedId, useMock])

  const nodeTypes = React.useMemo(() => ({ security: SecurityNode }), [])
  const edgeTypes = React.useMemo(() => ({ traffic: TrafficEdge }), [])

  const pushAlert = React.useCallback((a: Omit<AlertItem, "id" | "createdAt">) => {
    const item: AlertItem = {
      ...a,
      id: uid("alert"),
      createdAt: Date.now(),
    }
    setAlerts((prev) => [item, ...prev].slice(0, 20))
  }, [])

  const bumpPulse = React.useCallback((nodeId: string) => {
    setPulse((prev) => ({ ...prev, [nodeId]: Date.now() }))
  }, [])

  const applyTrustDelta = React.useCallback(
    (nodeId: string, delta: number, event: string) => {
      setNodes((prev) =>
        prev.map((n) => {
          if (n.id !== nodeId) return n
          const nextTrust = clamp(n.data.trustScore + delta, 0, 100)
          const nextRisk = riskFromTrust(nextTrust)
          return {
            ...n,
            data: {
              ...n.data,
              trustScore: nextTrust,
              risk: nextRisk,
              lastEvent: event,
              trustHistory: [...n.data.trustHistory, nowSeriesPoint(nextTrust)].slice(-24),
            },
          }
        })
      )
    },
    [setNodes]
  )

  const updateConnectedEdges = React.useCallback(() => {
    const riskByNode = new Map(nodes.map((n) => [n.id, n.data.risk] as const))

    setEdges((prev) => {
      const adjacency = new Map<string, string[]>()
      prev.forEach((e) => {
        if (!adjacency.has(e.source)) adjacency.set(e.source, [])
        adjacency.get(e.source)!.push(e.target)
      })

      const propagated = new Map<string, RiskLevel>()
      riskByNode.forEach((risk, id) => propagated.set(id, risk))

      const queue = [...propagated.entries()].filter(
        ([, r]) => r === "compromised" || r === "suspicious"
      )
      const visited = new Set<string>()
      for (const [id] of queue) visited.add(id)

      while (queue.length) {
        const [parentId, parentRisk] = queue.shift()!
        const children = adjacency.get(parentId) ?? []
        for (const childId of children) {
          if (visited.has(childId)) continue
          const childOwnRisk = riskByNode.get(childId) ?? "safe"
          if (childOwnRisk === "safe" && parentRisk !== "safe") {
            propagated.set(childId, parentRisk)
            visited.add(childId)
            queue.push([childId, parentRisk])
          }
        }
      }

      return prev.map((e) => {
        const src = propagated.get(e.source) ?? "safe"
        const dst = propagated.get(e.target) ?? "safe"
        const worst: RiskLevel =
          src === "compromised" || dst === "compromised"
            ? "compromised"
            : src === "suspicious" || dst === "suspicious"
              ? "suspicious"
              : "safe"
        return {
          ...e,
          data: {
            ...(e.data ?? {}),
            status: edgeStatusFromRisk(worst),
          },
        }
      })
    })
  }, [nodes, setEdges])

  React.useEffect(() => {
    updateConnectedEdges()
  }, [updateConnectedEdges])

  const deviceOptions: DeviceOption[] = React.useMemo(
    () =>
      nodes
        .filter((n) => n.data.kind === "device")
        .map((n) => ({ id: n.id, name: n.data.name })),
    [nodes]
  )

  const simulate = React.useCallback(
    async (type: SimulationType, deviceId: string, stealthLevel?: StealthLevel) => {
      const target = nodes.find((n) => n.id === deviceId)
      if (!target) return

      setSelectedId(target.id)
      bumpPulse(target.id)

      if (useMock) {
        const stealthPenalties: Record<StealthLevel, number> = { low: 50, medium: 35, high: 20 }
        const mockDetection: Record<StealthLevel, number> = { low: 85, medium: 50, high: 20 }
        const sl = stealthLevel ?? "medium"
        const basePenalty = type === "backdoor" ? stealthPenalties[sl] : Math.floor(Math.random() * 21) + 40
        const penalty = -basePenalty
        const deltas: Record<SimulationType, { title: string; desc: string; event: string }> = {
          backdoor: { title: "Backdoor behavior pattern", desc: `${target.data.name} exhibited persistence + beaconing indicators (stealth: ${sl}).`, event: `Backdoor simulation (${sl} stealth): persistence indicators detected` },
          traffic_spike: { title: "Traffic anomaly detected", desc: `${target.data.name} burst traffic signature observed.`, event: "Traffic spike simulation: anomaly score increased" },
          exfil: { title: "Possible data exfiltration", desc: `${target.data.name} shows high outbound volume to unknown host.`, event: "Exfiltration simulation: outbound risk elevated" },
          malware: { title: "Malware indicators", desc: `${target.data.name} triggered malicious process heuristics.`, event: "Malware simulation: behavior heuristic triggered" },
        }
        const d = deltas[type]
        const newTrust = clamp(target.data.trustScore + penalty, 0, 100)
        const sev = riskFromTrust(newTrust)
        pushAlert({
          title: d.title,
          description: d.desc,
          severity: sev,
          nodeId: target.id,
          ...(type === "backdoor" ? { detectionDifficulty: mockDetection[sl] } : {}),
        })
        applyTrustDelta(target.id, penalty, d.event)
        return
      }

      try {
        let response
        if (type === "backdoor") {
          response = await api.simulateBackdoor(target.id, stealthLevel ?? "medium")
        } else if (type === "traffic_spike") {
          response = await api.simulateTrafficSpike(target.id)
        } else if (type === "exfil") {
          response = await api.simulateExfiltration(target.id)
        } else {
          response = await api.simulateAttack({ device_id: target.id })
        }

        setNodes((prev) =>
          prev.map((n) => {
            if (n.id !== response.device_id) return n
            const newTrust = response.new_trust_score
            const newRisk = mapRiskLevel(response.new_risk_level)
            return {
              ...n,
              data: {
                ...n.data,
                trustScore: newTrust,
                risk: newRisk,
                lastEvent: response.message,
                trustHistory: [
                  ...n.data.trustHistory,
                  nowSeriesPoint(newTrust),
                ].slice(-24),
              },
            }
          })
        )

        pushAlert({
          title: response.attack_type.replace(/_/g, " "),
          description: response.message,
          severity: mapRiskLevel(response.new_risk_level),
          nodeId: response.device_id,
          ...(response.detection_difficulty != null ? { detectionDifficulty: response.detection_difficulty } : {}),
        })

        try {
          const apiAlerts = await api.alerts()
          setAlerts(apiAlerts.map(mapAlertFromAPI))
        } catch {}
      } catch (err) {
        console.error("API simulation failed, falling back to local:", err)
        const penalty = -(Math.floor(Math.random() * 21) + 40)
        const deltas: Record<SimulationType, { title: string; desc: string; event: string }> = {
          backdoor: { title: "Backdoor behavior pattern", desc: `${target.data.name} exhibited persistence + beaconing indicators.`, event: "Backdoor simulation: persistence indicators detected" },
          traffic_spike: { title: "Traffic anomaly detected", desc: `${target.data.name} burst traffic signature observed.`, event: "Traffic spike simulation: anomaly score increased" },
          exfil: { title: "Possible data exfiltration", desc: `${target.data.name} shows high outbound volume to unknown host.`, event: "Exfiltration simulation: outbound risk elevated" },
          malware: { title: "Malware indicators", desc: `${target.data.name} triggered malicious process heuristics.`, event: "Malware simulation: behavior heuristic triggered" },
        }
        const d = deltas[type]
        const newTrust = clamp(target.data.trustScore + penalty, 0, 100)
        const sev = riskFromTrust(newTrust)
        pushAlert({ title: d.title, description: d.desc, severity: sev, nodeId: target.id })
        applyTrustDelta(target.id, penalty, d.event)
      }
    },
    [applyTrustDelta, bumpPulse, nodes, pushAlert, setNodes, useMock]
  )

  const resetNetwork = React.useCallback(async () => {
    setResetting(true)
    try {
      if (useMock) {
        loadMock()
      } else {
        await api.resetNetwork()
        await loadFromAPI()
      }
      setAlerts([])
      setSelectedId(null)
      setDeviceDetail(null)
    } catch (err) {
      console.error("Reset network failed:", err)
    } finally {
      setResetting(false)
    }
  }, [useMock, loadFromAPI, loadMock])

  const handleLayoutChange = React.useCallback(
    (mode: LayoutMode) => {
      setLayoutMode(mode)
      const currentNodes = nodesRef.current
      const currentEdges = edgesRef.current
      let result: { nodes: Node<DeviceNodeData>[]; edges: Edge<TrafficEdgeData>[] }
      if (mode === "radial") {
        result = applyRadialLayout(currentNodes, currentEdges)
      } else {
        const direction = mode === "vertical" ? "TB" : "LR"
        result = applyDagreLayout(currentNodes, currentEdges, direction)
      }
      setNodes(result.nodes)
      setEdges(result.edges)
      setTimeout(() => fitView({ padding: 0.22, duration: 300 }), 50)
    },
    [setNodes, setEdges, fitView]
  )

  if (loading) {
    return (
      <div className="relative h-dvh w-dvw overflow-hidden cyber-canvas-bg">
        <div className="pointer-events-none absolute inset-0 cyber-canvas-radial" />
        <CanvasSkeleton />
      </div>
    )
  }

  return (
    <div className="relative h-dvh w-dvw overflow-hidden cyber-canvas-bg">
      <div className="pointer-events-none absolute inset-0 cyber-canvas-radial" />

      <TopToolbar
        trustScore={trustScore}
        alerts={alerts}
        devices={deviceOptions}
        useMock={useMock}
        onToggleMock={() => {
          setLoading(true)
          setUseMock((v) => !v)
        }}
        onAddDevice={() => setAddDeviceOpen(true)}
        onSimulate={simulate}
        onResetNetwork={resetNetwork}
        resetting={resetting}
      />
      <DetailPanel node={selectedNode} alerts={alerts} deviceDetail={deviceDetail} onClose={() => setSelectedId(null)} />
      <AddDeviceModal
        open={addDeviceOpen}
        useMock={useMock}
        existingDevices={deviceOptions}
        onClose={() => setAddDeviceOpen(false)}
        onAdded={refreshCanvas}
      />

      <div className="absolute inset-0">
        <ReactFlow
          nodes={nodes.map((n) => {
            const isRouter = n.data.isHub
            const isAffected = n.data.risk === "compromised" || n.data.risk === "suspicious"
            const muted =
              hasCompromised && !isRouter && !isAffected
            return {
              ...n,
              data: { ...n.data, pulseAt: pulse[n.id], muted },
            }
          })}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => setSelectedId(node.id)}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.22 }}
          defaultViewport={{ x: 0, y: 0, zoom: 0.9 }}
          minZoom={0.25}
          maxZoom={1.85}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={26}
            size={1}
            color="rgba(26,43,43,0.1)"
          />

          <div className="pointer-events-none absolute left-4 bottom-4 z-30">
            <div className="pointer-events-auto rounded-2xl border border-white/10 bg-zinc-950/60 px-5 py-3.5 text-[13px] text-zinc-300 shadow-[0_14px_45px_rgba(0,0,0,0.7)] backdrop-blur-md" style={{ fontFamily: '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif' }}>
              <div className="text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
                Network breakdown
              </div>
              <div className="mt-2.5 grid grid-cols-2 gap-x-6 gap-y-2">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-zinc-400">Devices</span>
                  <span className="font-semibold tabular-nums text-zinc-100">
                    {stats.total}
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-zinc-400">Safe</span>
                  <span className="font-semibold tabular-nums text-emerald-300">
                    {stats.safe}
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-zinc-400">Suspicious</span>
                  <span className="font-semibold tabular-nums text-orange-300">
                    {stats.suspicious}
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-zinc-400">Compromised</span>
                  <span className="font-semibold tabular-nums text-red-300">
                    {stats.compromised}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="absolute bottom-4 right-4 z-30">
            <div
              className="pointer-events-auto flex items-center gap-1 rounded-xl border border-white/10 bg-zinc-950/60 p-1 shadow-[0_14px_45px_rgba(0,0,0,0.7)] backdrop-blur-md"
              style={{ fontFamily: '"Calibri","Segoe UI",system-ui,-apple-system,sans-serif' }}
            >
              {(["radial", "vertical", "horizontal"] as LayoutMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleLayoutChange(mode)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors capitalize",
                    layoutMode === mode
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/30"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5 border border-transparent"
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </ReactFlow>
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  )
}
