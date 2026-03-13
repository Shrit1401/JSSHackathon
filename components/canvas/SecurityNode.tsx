"use client"

import * as React from "react"
import { Handle, Position } from "reactflow"
import { motion } from "framer-motion"
import {
  Activity,
  Bell,
  Camera,
  Cpu,
  Laptop,
  Printer,
  Router,
  Shield,
  Tv,
  Zap,
} from "lucide-react"

import type { DeviceNodeData, RiskLevel } from "@/components/canvas/types"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n))
}

function riskToStyles(risk: RiskLevel) {
  switch (risk) {
    case "safe":
      return {
        border: "border-emerald-400/20",
        glow: "",
        badge: "green" as const,
        ring: "stroke-emerald-400",
        ringBg: "stroke-emerald-400/15",
      }
    case "suspicious":
      return {
        border: "border-orange-400/25 hover:border-orange-300/45",
        glow: "hover:shadow-[0_0_0_1px_rgba(251,146,60,0.18),0_12px_30px_rgba(0,0,0,0.35)]",
        badge: "orange" as const,
        ring: "stroke-orange-400",
        ringBg: "stroke-orange-400/15",
      }
    case "compromised":
      return {
        border: "border-red-400/25 hover:border-red-300/45",
        glow: "hover:shadow-[0_0_0_1px_rgba(248,113,113,0.2),0_12px_30px_rgba(0,0,0,0.35)]",
        badge: "red" as const,
        ring: "stroke-red-400",
        ringBg: "stroke-red-400/15",
      }
  }
}

function Icon({ icon }: { icon: DeviceNodeData["icon"] }) {
  const className = "size-4 text-zinc-200"
  switch (icon) {
    case "router":
      return <Router className={className} />
    case "camera":
      return <Camera className={className} />
    case "printer":
      return <Printer className={className} />
    case "laptop":
      return <Laptop className={className} />
    case "tv":
      return <Tv className={className} />
    case "sensor":
      return <Cpu className={className} />
    case "engine":
      return <Shield className={className} />
    case "alert":
      return <Bell className={className} />
    case "action":
      return <Zap className={className} />
    default:
      return <Activity className={className} />
  }
}

function TrustRing({
  value,
  risk,
}: {
  value: number
  risk: RiskLevel
}) {
  const r = 12
  const c = 2 * Math.PI * r
  const pct = clamp(value, 0, 100) / 100
  const dash = c * pct
  const styles = riskToStyles(risk)

  return (
    <div className="relative grid size-8 place-items-center">
      <svg viewBox="0 0 32 32" className="size-8 -rotate-90">
        <circle
          cx="16"
          cy="16"
          r={r}
          fill="none"
          strokeWidth="3"
          className={styles.ringBg}
        />
        <motion.circle
          cx="16"
          cy="16"
          r={r}
          fill="none"
          strokeWidth="3"
          strokeLinecap="round"
          className={styles.ring}
          initial={false}
          animate={{
            strokeDasharray: `${dash} ${c - dash}`,
          }}
          transition={{ type: "spring", stiffness: 220, damping: 28 }}
        />
      </svg>
      <div className="absolute text-[10px] font-medium tabular-nums text-zinc-200">
        {Math.round(value)}
      </div>
    </div>
  )
}

export function SecurityNode({
  data,
  selected,
}: {
  data: DeviceNodeData
  selected?: boolean
}) {
  const styles = riskToStyles(data.risk)
  const isCompromised = data.risk === "compromised"
  const subtleSelected = selected
    ? "ring-1 ring-cyan-300/35 shadow-[0_0_0_1px_rgba(34,211,238,0.15),0_24px_60px_rgba(0,0,0,0.55)]"
    : ""
  const pulsingRecent = data.pulseAt ? Date.now() - data.pulseAt < 1600 : false
  const shouldPulse = isCompromised || pulsingRecent

  return (
    <motion.div
      layout
      initial={false}
      whileHover={{ y: -2 }}
      animate={
        shouldPulse
          ? {
              boxShadow: [
                "0 10px 30px rgba(0,0,0,0.4)",
                "0 0 0 2px rgba(248,113,113,0.6), 0 0 30px rgba(248,113,113,0.9)",
                "0 10px 30px rgba(0,0,0,0.4)",
              ],
            }
          : undefined
      }
      transition={{
        type: "spring",
        stiffness: 320,
        damping: 26,
        boxShadow: { duration: 0.9, ease: "easeInOut" },
      }}
      className={cn(
        "relative rounded-2xl border bg-zinc-950/55 px-3.5 py-3 shadow-[0_10px_30px_rgba(0,0,0,0.45)] backdrop-blur-md",
        "text-zinc-100",
        data.isHub ? "w-[260px]" : "w-[230px]",
        "transition-colors",
        styles.border,
        styles.glow,
        subtleSelected,
        data.risk === "safe" && !data.isHub ? "opacity-70" : "",
        data.muted ? "opacity-35" : ""
      )}
      style={{
        fontFamily: '"Calibri","Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,sans-serif',
      }}
    >
      {data.isHub ? (
        <>
          <Handle type="source" id="top" position={Position.Top} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="top-right" position={Position.Top} className="!size-1 !border-0 !bg-transparent" style={{ left: "75%" }} />
          <Handle type="source" id="top-left" position={Position.Top} className="!size-1 !border-0 !bg-transparent" style={{ left: "25%" }} />
          <Handle type="source" id="right" position={Position.Right} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="bottom-right" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" style={{ left: "75%" }} />
          <Handle type="source" id="bottom" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="bottom-left" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" style={{ left: "25%" }} />
          <Handle type="source" id="left" position={Position.Left} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-top" position={Position.Top} className="!size-1 !border-0 !bg-transparent" style={{ left: "50%" }} />
          <Handle type="source" id="source-right" position={Position.Right} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-bottom" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" style={{ left: "50%" }} />
          <Handle type="source" id="source-left" position={Position.Left} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-top" position={Position.Top} className="!size-1 !border-0 !bg-transparent" style={{ left: "50%" }} />
          <Handle type="target" id="target-right" position={Position.Right} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-left" position={Position.Left} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-bottom" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" style={{ left: "50%" }} />
        </>
      ) : (
        <>
          <Handle type="target" id="target-top" position={Position.Top} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-left" position={Position.Left} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-bottom" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="target" id="target-right" position={Position.Right} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-top" position={Position.Top} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-right" position={Position.Right} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-bottom" position={Position.Bottom} className="!size-1 !border-0 !bg-transparent" />
          <Handle type="source" id="source-left" position={Position.Left} className="!size-1 !border-0 !bg-transparent" />
        </>
      )}

      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <div className="grid size-8 place-items-center rounded-xl border border-white/10 bg-zinc-900/40">
            <Icon icon={data.icon} />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold tracking-tight">
              {data.name}
            </div>
            <div className="truncate text-xs text-zinc-400">
              {data.deviceType}
            </div>
          </div>
        </div>
        <TrustRing value={data.trustScore} risk={data.risk} />
      </div>

      <div className="mt-3 flex items-center justify-between gap-2">
        <div className="text-xs text-zinc-400">
          Trust{" "}
          <span className="font-medium text-zinc-200 tabular-nums">
            {Math.round(data.trustScore)}%
          </span>
        </div>
        <Badge variant={styles.badge} className="capitalize">
          {data.risk}
        </Badge>
      </div>

      {data.lastEvent ? (
        <div className="mt-2 truncate text-[11px] text-zinc-500">
          {data.lastEvent}
        </div>
      ) : null}
    </motion.div>
  )
}

