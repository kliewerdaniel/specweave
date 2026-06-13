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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import type { Spec, Delegation, MCPTool } from "@/types"

export default function AgentMonitorPage() {
  const [specs, setSpecs] = useState<Spec[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [delegations, setDelegations] = useState<Delegation[]>([])
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [toolResult, setToolResult] = useState<string | null>(null)

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
      .listDelegations(selectedId)
      .then((data) => setDelegations(data.delegations))
      .catch(() => setDelegations([]))
  }, [selectedId])

  useEffect(() => {
    api
      .mcpTools()
      .then((data) => setMcpTools(data.tools))
      .catch(() => setMcpTools([]))
  }, [])

  async function handleExecuteTool(tool: string) {
    setToolResult(null)
    try {
      const result = await api.mcpExecute(tool, { spec_id: selectedId })
      setToolResult(JSON.stringify(result.result, null, 2))
    } catch (e) {
      setToolResult(
        e instanceof Error ? `Error: ${e.message}` : "Execution failed"
      )
    }
  }

  const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    pending: "secondary",
    accepted: "outline",
    completed: "default",
    failed: "destructive",
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Agent Monitor</h1>
        <p className="text-muted-foreground mt-1">
          A2A/MCP connections, delegation states, and tools
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

        <div className="flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
            Pending
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500 inline-block" />
            Accepted
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
            Completed
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
            Failed
          </span>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Delegations</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : delegations.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No delegations found for this spec.
            </p>
          ) : (
            <ScrollArea className="h-[300px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Target Agent</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {delegations.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell className="font-mono text-xs">
                        {d.id.slice(0, 8)}...
                      </TableCell>
                      <TableCell>{d.target_agent}</TableCell>
                      <TableCell>
                        <Badge variant={statusVariant[d.status] || "secondary"}>
                          {d.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {new Date(d.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-xs max-w-[200px] truncate">
                        {d.result || "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>MCP Tools</CardTitle>
          </CardHeader>
          <CardContent>
            {mcpTools.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No MCP tools registered.
              </p>
            ) : (
              <div className="space-y-2">
                {mcpTools.map((tool) => (
                  <div
                    key={tool.name}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-sm">{tool.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {tool.description}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleExecuteTool(tool.name)}
                    >
                      Run
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>A2A Discovery</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full"
                onClick={async () => {
                  try {
                    const result = await api.a2aDiscover()
                    setToolResult(
                      JSON.stringify(result.specs, null, 2)
                    )
                  } catch (e) {
                    setToolResult(
                      e instanceof Error
                        ? `Error: ${e.message}`
                        : "Discovery failed"
                    )
                  }
                }}
              >
                Discover Specs (A2A)
              </Button>
              <p className="text-xs text-muted-foreground">
                Query the A2A endpoint to discover available specs and their
                statuses.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {toolResult && (
        <Card>
          <CardHeader>
            <CardTitle>Tool Result</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[200px]">
              <pre className="text-xs font-mono whitespace-pre-wrap">
                {toolResult}
              </pre>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
