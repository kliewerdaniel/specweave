"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { SpecGraph } from "@/components/spec-graph"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { Spec } from "@/types"

export default function SpecGraphPage() {
  const [specs, setSpecs] = useState<Spec[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [adjacency, setAdjacency] = useState<Record<string, string[]>>({})
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listSpecs()
      .then((data) => {
        setSpecs(data.specs)
        if (data.specs.length > 0) {
          setSelectedId(data.specs[0].id)
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setLoadingGraph(true)
    Promise.all([
      api.getGraph(selectedId),
      api.getGates(selectedId),
    ])
      .then(([graphData, gatesData]) => {
        setAdjacency(graphData.adjacency)
        const ns: Record<string, string> = {}
        const spec = specs.find((s) => s.id === selectedId)
        if (spec) ns[spec.id] = spec.status
        for (const gate of gatesData.gates) {
          ns[`gate-${gate.gate_id}`] = gate.status
        }
        setNodeStatuses(ns)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoadingGraph(false))
  }, [selectedId, specs])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Spec Graph</h1>
        <p className="text-muted-foreground mt-1">
          Interactive knowledge graph visualization
        </p>
      </div>

      <div className="flex items-center gap-4">
        <Select value={selectedId} onValueChange={(v) => v && setSelectedId(v)}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a spec" />
          </SelectTrigger>
          <SelectContent>
            {specs.map((spec) => (
              <SelectItem key={spec.id} value={spec.id}>
                {spec.project_title} ({spec.id})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-500 inline-block" />
            Pass
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" />
            Pending
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
            Fail
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950 rounded-lg text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>
            {selectedId
              ? specs.find((s) => s.id === selectedId)?.project_title ||
                selectedId
              : "Graph View"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading || loadingGraph ? (
            <Skeleton className="h-[600px] w-full" />
          ) : Object.keys(adjacency).length === 0 ? (
            <div className="flex items-center justify-center h-[600px] text-muted-foreground">
              No graph data available for this spec
            </div>
          ) : (
            <SpecGraph adjacency={adjacency} nodeStatuses={nodeStatuses} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
