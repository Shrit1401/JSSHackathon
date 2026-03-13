"use client"

import * as React from "react"
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "reactflow"

import type { TrafficEdgeData } from "@/components/canvas/types"

type Props = {
  id: string
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourcePosition: any
  targetPosition: any
  data?: TrafficEdgeData
  markerEnd?: string
}

function edgeColor(status: TrafficEdgeData["status"] | undefined) {
  switch (status) {
    case "suspicious":
      return "rgba(251,146,60,0.72)"
    case "compromised":
      return "rgba(248,113,113,0.78)"
    case "normal":
    default:
      return "rgba(34,211,238,0.45)"
  }
}

function dotColor(status: TrafficEdgeData["status"] | undefined) {
  switch (status) {
    case "suspicious":
      return "fill-orange-300/90"
    case "compromised":
      return "fill-red-300/90"
    case "normal":
    default:
      return "fill-cyan-200/90"
  }
}

export function TrafficEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: Props) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  })

  const status = data?.status ?? "normal"
  const dur = Math.max(1.8, Math.min(5.5, (data?.speed ?? 3.2)))
  const pathId = `edgepath-${id}`

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: edgeColor(status),
          strokeWidth:
            status === "compromised" ? 4 : status === "suspicious" ? 3 : 2,
          filter:
            status === "compromised"
              ? "drop-shadow(0 0 10px rgba(248,113,113,0.2))"
              : status === "suspicious"
                ? "drop-shadow(0 0 10px rgba(251,146,60,0.14))"
                : "drop-shadow(0 0 10px rgba(34,211,238,0.10))",
          strokeDasharray: "none",
        }}
      />

      <EdgeLabelRenderer>
        <svg className="absolute left-0 top-0 h-full w-full overflow-visible pointer-events-none">
          <defs>
            <path id={pathId} d={edgePath} />
          </defs>
          {(status === "suspicious" || status === "compromised") && (
            <circle r="2.2" className={dotColor(status)}>
              <animateMotion
                dur={`${dur}s`}
                repeatCount="indefinite"
                rotate="auto"
                keyTimes="0;1"
                keySplines="0.4 0 0.2 1"
                calcMode="spline"
              >
                <mpath href={`#${pathId}`} />
              </animateMotion>
            </circle>
          )}
          {data?.label ? (
            <text
              fontSize="10"
              fill="rgba(248,250,252,0.85)"
              letterSpacing="0.03em"
            >
              <textPath href={`#${pathId}`} startOffset="50%" textAnchor="middle">
                {data.label}
              </textPath>
            </text>
          ) : null}
        </svg>
      </EdgeLabelRenderer>
    </>
  )
}

