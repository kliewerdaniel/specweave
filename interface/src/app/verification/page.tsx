"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import type { Spec, VerificationGate } from "@/types"

const GATE_LABELS: Record<string, string> = {
  gate1_completeness: "Spec Completeness",
  gate2_consistency: "Internal Consistency",
  gate3_dependencies: "Dependency Resolution",
  gate4_constraints: "Constraint Satisfaction",
  gate5_coherence: "Architecture Coherence",
  gate6_readiness: "Code Generation Readiness",
}

export default function VerificationPage() {
  const [specs, setSpecs] = useState<Spec[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [gates, setGates] = useState<VerificationGate[]>([])
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
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
    api
      .getGates(selectedId)
      .then((data) => setGates(data.gates))
      .catch(() => setGates([]))
  }, [selectedId])

  async function handleVerify() {
    if (!selectedId) return
    setVerifying(true)
    setError(null)
    try {
      const result = await api.verifySpec(selectedId)
      setGates(result.gates)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed")
    } finally {
      setVerifying(false)
    }
  }

  async function handleCompile() {
    if (!selectedId) return
    setVerifying(true)
    setError(null)
    try {
      const result = await api.compileSpec(selectedId)
      setGates(result.gates)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compilation failed")
    } finally {
      setVerifying(false)
    }
  }

  const passedCount = gates.filter((g) => g.status === "passed").length
  const failedCount = gates.filter((g) => g.status === "failed").length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Verification Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Gate-by-gate verification status with failure traces
        </p>
      </div>

      <div className="flex items-end gap-4 flex-wrap">
        <div className="space-y-2">
          <label className="text-sm font-medium">Spec</label>
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
        </div>

        <Button onClick={handleVerify} disabled={verifying || !selectedId}>
          {verifying ? "Running..." : "Verify"}
        </Button>
        <Button
          onClick={handleCompile}
          disabled={verifying || !selectedId}
          variant="outline"
        >
          {verifying ? "Running..." : "Full Compile"}
        </Button>
      </div>

      {error && (
        <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950 rounded-lg text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Gates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{gates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Passed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {passedCount}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">
              {failedCount}
            </div>
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : gates.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No Verification Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">
              Run a verification or full compilation to see gate results.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {gates.map((gate) => {
            const label =
              GATE_LABELS[gate.gate_id] ||
              gate.gate_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
            return (
              <Card
                key={gate.id}
                className={
                  gate.status === "passed"
                    ? "border-green-300"
                    : gate.status === "failed"
                      ? "border-red-300"
                      : ""
                }
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{label}</span>
                        <Badge
                          variant={
                            gate.status === "passed"
                              ? "default"
                              : gate.status === "failed"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {gate.status}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Gate ID: {gate.gate_id}
                      </div>
                      {gate.checked_at && (
                        <div className="text-xs text-muted-foreground mt-0.5">
                          Checked: {new Date(gate.checked_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>

                  {gate.status === "failed" && gate.failure_reason && (
                    <>
                      <Separator className="my-3" />
                      <div className="text-sm">
                        <span className="font-medium text-red-600">
                          Failure Reason:{" "}
                        </span>
                        <span className="text-muted-foreground">
                          {gate.failure_reason}
                        </span>
                      </div>
                      {gate.failure_location && (
                        <div className="mt-2 p-2 bg-muted rounded text-xs font-mono overflow-x-auto">
                          {JSON.stringify(gate.failure_location, null, 2)}
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
