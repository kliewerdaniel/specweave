export interface Spec {
  id: string
  project_name: string
  project_title: string
  project_description: string
  version: string
  status: string
  created_at: string
  updated_at: string
  raw_spec: string
  graph_snapshot: Record<string, unknown> | null
  verification_report: Record<string, unknown> | null
}

export interface VerificationGate {
  id: string
  spec_id: string
  gate_id: string
  status: "pending" | "passed" | "failed"
  failure_reason: string | null
  failure_location: Record<string, unknown> | null
  checked_at: string
}

export interface Speculation {
  id: string
  spec_id: string
  section_id: string
  candidate_index: number
  architecture_description: string
  constraint_scores: Record<string, number>
  status: "drafted" | "verified" | "committed" | "rejected"
  rejection_reason: string | null
  created_at: string
}

export interface Delegation {
  id: string
  spec_id: string
  sub_spec_content: string
  target_agent: string
  status: "pending" | "accepted" | "completed" | "failed"
  result: string | null
  created_at: string
}

export interface AuditRecord {
  id: string
  spec_id: string
  action: string
  actor: string
  details: Record<string, unknown>
  created_at: string
}

export interface SpecDetail {
  spec: Spec
  graph: Record<string, string[]>
  verification: VerificationGate[]
}

export interface CompilationResult {
  spec_id: string
  gates: VerificationGate[]
  status: string
}

export interface SpeculationResult {
  candidates: Speculation[]
}

export interface VerificationResult {
  spec_id: string
  gates: VerificationGate[]
  passed: boolean
}

export interface GraphNode {
  id: string
  type: string
  label: string
  verification_status?: "pass" | "fail" | "pending"
}

export interface GraphEdge {
  source: string
  target: string
  type: string
}

export interface MCPTool {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export interface HealthStatus {
  status: string
  version: string
}
