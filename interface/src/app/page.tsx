"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { Spec, VerificationGate } from "@/types"

export default function Dashboard() {
  const [specs, setSpecs] = useState<Spec[]>([])
  const [gatesMap, setGatesMap] = useState<Record<string, VerificationGate[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await api.listSpecs()
        setSpecs(data.specs)
        const gm: Record<string, VerificationGate[]> = {}
        for (const s of data.specs) {
          try {
            const g = await api.getGates(s.id)
            gm[s.id] = g.gates
          } catch {
            gm[s.id] = []
          }
        }
        setGatesMap(gm)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const totalGates = Object.values(gatesMap).flat().length
  const passedGates = Object.values(gatesMap)
    .flat()
    .filter((g) => g.status === "passed").length
  const failedGates = Object.values(gatesMap)
    .flat()
    .filter((g) => g.status === "failed").length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          SpecWeave — Self-verifying spec-driven development engine
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Specs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-3xl font-bold">{specs.length}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gates Passed
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-3xl font-bold text-green-600">
                {passedGates}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gates Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-3xl font-bold text-red-600">
                {failedGates}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Gates
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-3xl font-bold">{totalGates}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {error && (
        <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950 rounded-lg text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Specs Overview</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : specs.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No specs found. Create one via the API.
            </p>
          ) : (
            <div className="space-y-2">
              {specs.map((spec) => (
                <div
                  key={spec.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{spec.project_title}</div>
                    <div className="text-xs text-muted-foreground">
                      {spec.id} v{spec.version}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        spec.status === "verified" || spec.status === "compiled"
                          ? "default"
                          : spec.status === "failed"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {spec.status}
                    </Badge>
                    {(gatesMap[spec.id]?.length ?? 0) > 0 && (
                      <span className="text-xs text-muted-foreground">
                        {gatesMap[spec.id].filter((g) => g.status === "passed").length}/
                        {gatesMap[spec.id].length} gates
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
