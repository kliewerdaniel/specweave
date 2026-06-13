const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v2"

interface FetchOptions extends RequestInit {
  params?: Record<string, string>
}

async function getAuthToken(): Promise<string | null> {
  const stored = localStorage.getItem("specweave_token")
  return stored
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...fetchOpts } = options

  let url = `${BASE_URL}${path}`
  if (params) {
    const qs = new URLSearchParams(params).toString()
    url += `?${qs}`
  }

  const token = await getAuthToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOpts.headers as Record<string, string>),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(url, { ...fetchOpts, headers })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }

  return res.json()
}

export const api = {
  health: () => request<{ status: string; version: string }>("/health"),

  listSpecs: () => request<{ specs: import("@/types").Spec[] }>("/specs"),

  getSpec: (id: string) =>
    request<import("@/types").SpecDetail>(`/specs/${id}`),

  createSpec: (data: Record<string, unknown>) =>
    request<import("@/types").Spec>("/specs", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  compileSpec: (id: string) =>
    request<import("@/types").CompilationResult>(`/specs/${id}/compile`, {
      method: "POST",
    }),

  speculateSpec: (id: string, sectionId: string) =>
    request<import("@/types").SpeculationResult>(`/specs/${id}/speculate`, {
      method: "POST",
      body: JSON.stringify({ section_id: sectionId }),
    }),

  verifySpec: (id: string) =>
    request<import("@/types").VerificationResult>(`/specs/${id}/verify`, {
      method: "POST",
    }),

  getGates: (id: string) =>
    request<{ gates: import("@/types").VerificationGate[] }>(
      `/specs/${id}/gates`
    ),

  listDelegations: (id: string) =>
    request<{ delegations: import("@/types").Delegation[] }>(
      `/specs/${id}/delegates`
    ),

  createDelegation: (
    id: string,
    data: { sub_spec_content: string; target_agent: string }
    ) =>
    request<import("@/types").Delegation>(`/specs/${id}/delegates`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getGraph: (id: string) =>
    request<{ adjacency: Record<string, string[]> }>(`/specs/${id}/graph`),

  getAuditTrail: (id: string) =>
    request<{ records: import("@/types").AuditRecord[] }>(
      `/specs/${id}/audit`
    ),

  a2aDiscover: () =>
    request<{ specs: import("@/types").Spec[] }>("/a2a/specs"),

  a2aDelegate: (data: {
    spec_id: string
    sub_spec_content: string
    target_agent: string
  }) =>
    request<import("@/types").Delegation>("/a2a/delegate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  a2aSubmit: (data: { delegation_id: string; result: string }) =>
    request<{ delegation: import("@/types").Delegation }>("/a2a/submit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  mcpTools: () =>
    request<{ tools: import("@/types").MCPTool[] }>("/mcp/tools"),

  mcpExecute: (tool: string, params: Record<string, unknown>) =>
    request<{ result: unknown }>("/mcp/execute", {
      method: "POST",
      body: JSON.stringify({ tool, params }),
    }),
}
