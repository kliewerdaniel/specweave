"use client"

import { useEffect, useRef, useState } from "react"

interface GraphNode {
  id: string
  type: string
  label: string
  verification_status?: "pass" | "fail" | "pending"
}

interface GraphEdge {
  source: string
  target: string
  type: string
}

interface SpecGraphProps {
  adjacency: Record<string, string[]>
  nodeStatuses?: Record<string, string>
}

export function SpecGraph({ adjacency, nodeStatuses = {} }: SpecGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])

  useEffect(() => {
    const nodeSet = new Set<string>()
    const edgeList: GraphEdge[] = []
    const nodeList: GraphNode[] = []

    for (const [source, targets] of Object.entries(adjacency)) {
      nodeSet.add(source)
      for (const target of targets) {
        nodeSet.add(target)
        edgeList.push({ source, target, type: "depends_on" })
      }
    }

    const statusMap: Record<string, string> = {
      verified: "pass",
      compiled: "pass",
      active: "pending",
      draft: "pending",
      failed: "fail",
    }

    for (const id of nodeSet) {
      const status = nodeStatuses[id] || statusMap[id] || "pending"
      nodeList.push({
        id,
        type: "spec_section",
        label: id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        verification_status: status as "pass" | "fail" | "pending",
      })
    }

    setNodes(nodeList)
    setEdges(edgeList)
  }, [adjacency, nodeStatuses])

  const statusColors: Record<string, string> = {
    pass: "fill-green-500",
    fail: "fill-red-500",
    pending: "fill-yellow-500",
  }

  const nodePositions = useRef<Record<string, { x: number; y: number }>>({})
  const [positions, setPositions] = useState<
    Record<string, { x: number; y: number }>
  >({})
  const animFrame = useRef<number | null>(null)

  useEffect(() => {
    const w = containerRef.current?.clientWidth || 800
    const h = containerRef.current?.clientHeight || 600
    const centerX = w / 2
    const centerY = h / 2

    const initPos: Record<string, { x: number; y: number }> = {}
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      initPos[n.id] = {
        x: centerX + 200 * Math.cos(angle),
        y: centerY + 200 * Math.sin(angle),
      }
    })
    nodePositions.current = initPos
    setPositions({ ...initPos })

    const k = 0.05
    const repulsion = 8000
    const attraction = 0.005

    function tick() {
      const pos = nodePositions.current
      const forces: Record<string, { fx: number; fy: number }> = {}

      for (const n of nodes) {
        forces[n.id] = { fx: 0, fy: 0 }
      }

      for (const a of nodes) {
        for (const b of nodes) {
          if (a.id === b.id) continue
          const dx = pos[a.id].x - pos[b.id].x
          const dy = pos[a.id].y - pos[b.id].y
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 10)
          const force = repulsion / (dist * dist)
          forces[a.id].fx += (dx / dist) * force
          forces[a.id].fy += (dy / dist) * force
        }
      }

      for (const edge of edges) {
        const s = pos[edge.source]
        const t = pos[edge.target]
        if (!s || !t) continue
        const dx = t.x - s.x
        const dy = t.y - s.y
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 10)
        forces[edge.source].fx += dx * attraction
        forces[edge.source].fy += dy * attraction
        forces[edge.target].fx -= dx * attraction
        forces[edge.target].fy -= dy * attraction
      }

      for (const n of nodes) {
        pos[n.id] = {
          x: pos[n.id].x + forces[n.id].fx * k,
          y: pos[n.id].y + forces[n.id].fy * k,
        }
        pos[n.id].x = Math.max(20, Math.min(w - 20, pos[n.id].x))
        pos[n.id].y = Math.max(20, Math.min(h - 20, pos[n.id].y))
      }

      setPositions({ ...pos })

      if (nodes.length > 0) {
        animFrame.current = requestAnimationFrame(tick)
      }
    }

    animFrame.current = requestAnimationFrame(tick)
    return () => {
      if (animFrame.current) cancelAnimationFrame(animFrame.current)
    }
  }, [nodes, edges])

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No graph data available
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[600px] border rounded-lg overflow-hidden bg-card"
    >
      <svg width="100%" height="100%" className="absolute inset-0">
        {edges.map((edge, i) => {
          const s = positions[edge.source]
          const t = positions[edge.target]
          if (!s || !t) return null
          return (
            <line
              key={`edge-${i}`}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              stroke="currentColor"
              className="text-muted-foreground/30"
              strokeWidth={1.5}
            />
          )
        })}
        {nodes.map((node) => {
          const pos = positions[node.id]
          if (!pos) return null
          const isSelected = selectedNode === node.id
          const colorClass =
            statusColors[node.verification_status || "pending"]
          return (
            <g
              key={node.id}
              onClick={() =>
                setSelectedNode(isSelected ? null : node.id)
              }
              className="cursor-pointer"
            >
              <circle
                cx={pos.x}
                cy={pos.y}
                r={isSelected ? 14 : 10}
                className={
                  isSelected
                    ? "fill-primary stroke-primary-foreground"
                    : colorClass
                }
                strokeWidth={isSelected ? 3 : 0}
              />
              <text
                x={pos.x}
                y={pos.y + 20}
                textAnchor="middle"
                className="fill-current text-[10px] text-muted-foreground"
              >
                {node.label}
              </text>
            </g>
          )
        })}
      </svg>
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 p-3 bg-popover border rounded-lg shadow-lg text-sm">
          <div className="font-medium">{nodes.find((n) => n.id === selectedNode)?.label}</div>
          <div className="text-muted-foreground">
            ID: {selectedNode} | Type: {nodes.find((n) => n.id === selectedNode)?.type} | Status:{" "}
            {nodes.find((n) => n.id === selectedNode)?.verification_status}
          </div>
        </div>
      )}
    </div>
  )
}
