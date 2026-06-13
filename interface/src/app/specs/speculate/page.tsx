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
import type { Spec, Speculation } from "@/types"

const SECTION_OPTIONS = [
  { id: "architecture", label: "Architecture" },
  { id: "data_models", label: "Data Models" },
  { id: "api_specification", label: "API Specification" },
]

export default function SpeculativeExplorerPage() {
  const [specs, setSpecs] = useState<Spec[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [selectedSection, setSelectedSection] = useState("architecture")
  const [candidates, setCandidates] = useState<Speculation[]>([])
  const [loading, setLoading] = useState(true)
  const [speculating, setSpeculating] = useState(false)
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

  async function handleSpeculate() {
    if (!selectedId) return
    setSpeculating(true)
    setError(null)
    try {
      const result = await api.speculateSpec(selectedId, selectedSection)
      setCandidates(result.candidates)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Speculation failed")
    } finally {
      setSpeculating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Speculative Explorer
        </h1>
        <p className="text-muted-foreground mt-1">
          Draft and compare alternative architectures
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

        <div className="space-y-2">
          <label className="text-sm font-medium">Section</label>
          <Select value={selectedSection} onValueChange={(v) => v && setSelectedSection(v)}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select section" />
            </SelectTrigger>
            <SelectContent>
              {SECTION_OPTIONS.map((opt) => (
                <SelectItem key={opt.id} value={opt.id}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button onClick={handleSpeculate} disabled={speculating || !selectedId}>
          {speculating ? "Speculating..." : "Run Speculation"}
        </Button>
      </div>

      {error && (
        <div className="p-4 border border-red-200 bg-red-50 dark:bg-red-950 rounded-lg text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : candidates.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No Speculations Yet</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">
              Select a spec and section, then click &ldquo;Run Speculation&rdquo; to
              generate architecture alternatives.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {candidates.map((candidate) => (
            <Card
              key={candidate.id}
              className={
                candidate.status === "committed"
                  ? "border-green-500 ring-1 ring-green-500"
                  : candidate.status === "rejected"
                    ? "border-red-300 opacity-75"
                    : ""
              }
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">
                    Candidate {candidate.candidate_index + 1}
                  </CardTitle>
                  <Badge
                    variant={
                      candidate.status === "committed"
                        ? "default"
                        : candidate.status === "rejected"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {candidate.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm leading-relaxed whitespace-pre-wrap line-clamp-6">
                  {candidate.architecture_description}
                </div>

                {candidate.constraint_scores &&
                  Object.keys(candidate.constraint_scores).length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h4 className="text-xs font-medium text-muted-foreground mb-2">
                          Constraint Scores
                        </h4>
                        <div className="space-y-1">
                          {Object.entries(candidate.constraint_scores).map(
                            ([key, score]) => (
                              <div
                                key={key}
                                className="flex items-center justify-between text-xs"
                              >
                                <span className="text-muted-foreground capitalize">
                                  {key.replace(/_/g, " ")}
                                </span>
                                <span
                                  className={
                                    (score as number) >= 0.7
                                      ? "text-green-600 font-medium"
                                      : (score as number) >= 0.4
                                        ? "text-yellow-600 font-medium"
                                        : "text-red-600 font-medium"
                                  }
                                >
                                  {((score as number) * 100).toFixed(0)}%
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    </>
                  )}

                {candidate.rejection_reason && (
                  <>
                    <Separator />
                    <div className="text-xs text-red-600">
                      <span className="font-medium">Rejected: </span>
                      {candidate.rejection_reason}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
