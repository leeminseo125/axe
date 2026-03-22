const AXENGINE_URL = process.env.NEXT_PUBLIC_AXENGINE_URL || "http://localhost:8001";
const AXE_POE_URL = process.env.NEXT_PUBLIC_AXE_POE_URL || "http://localhost:8002";
const POLICY_URL = process.env.NEXT_PUBLIC_POLICY_URL || "http://localhost:8003";
const POQAT_URL = process.env.NEXT_PUBLIC_POQAT_URL || "http://localhost:8004";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ---- AXEngine API ----

export async function getAXEngineHealth() {
  return fetchJSON<{
    service: string;
    status: string;
    llm_providers: string[];
  }>(`${AXENGINE_URL}/health`);
}

export async function getAXEngineStats() {
  return fetchJSON<{
    failure_rate_1h: number;
    connectors: string[];
    llm_providers: string[];
  }>(`${AXENGINE_URL}/stats`);
}

export async function getGoals(status?: string) {
  const params = status ? `?status=${status}` : "";
  return fetchJSON<
    Array<{
      id: string;
      title: string;
      status: string;
      priority: number;
      created_at: string;
    }>
  >(`${AXENGINE_URL}/goals${params}`);
}

export async function createGoal(data: {
  title: string;
  description?: string;
  priority?: number;
}) {
  return fetchJSON<{ id: string }>(`${AXENGINE_URL}/goals`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function planGoal(goalId: string) {
  return fetchJSON(`${AXENGINE_URL}/goals/${goalId}/plan`, { method: "POST" });
}

export async function executePlan(planId: string) {
  return fetchJSON(`${AXENGINE_URL}/plans/${planId}/execute`, {
    method: "POST",
  });
}

export async function getHITLStats() {
  return fetchJSON<{
    total_overrides: number;
    by_action: Record<string, number>;
    current_base_threshold: number;
  }>(`${AXENGINE_URL}/hitl/stats`);
}

export async function getConnectorsHealth() {
  return fetchJSON<Record<string, boolean>>(`${AXENGINE_URL}/connectors/health`);
}

// ---- AXE_POE API ----

export async function getPOEHealth() {
  return fetchJSON<{ service: string; status: string }>(
    `${AXE_POE_URL}/health`
  );
}

export async function getPOEStats() {
  return fetchJSON<{
    events_24h: number;
    insights_24h: number;
    pending_decisions: number;
    executions_24h: number;
  }>(`${AXE_POE_URL}/stats`);
}

export async function getInsights(severity?: string) {
  const params = severity ? `?severity=${severity}` : "";
  return fetchJSON<
    Array<{
      id: string;
      insight_type: string;
      severity: string;
      summary: string;
      created_at: string;
    }>
  >(`${AXE_POE_URL}/insights${params}`);
}

export async function getDecisions(status?: string) {
  const params = status ? `?status=${status}` : "";
  return fetchJSON<
    Array<{
      id: string;
      recommended_action: string;
      confidence: number;
      status: string;
      created_at: string;
    }>
  >(`${AXE_POE_URL}/decisions${params}`);
}

export async function approveDecision(decisionId: string) {
  return fetchJSON(`${AXE_POE_URL}/decisions/${decisionId}/approve`, {
    method: "POST",
  });
}

export async function runPipeline(windowMinutes: number = 60) {
  return fetchJSON<{
    events_captured: number;
    insights_generated: number;
    decisions_made: number;
    executions_run: number;
    feedbacks_recorded: number;
  }>(`${AXE_POE_URL}/pipeline/run?window_minutes=${windowMinutes}`, {
    method: "POST",
  });
}

export async function getEvents(source?: string) {
  const params = source ? `?source=${source}` : "";
  return fetchJSON<
    Array<{
      id: string;
      source: string;
      event_type: string;
      captured_at: string;
    }>
  >(`${AXE_POE_URL}/events${params}`);
}

// ---- Policy Engine API ----

export async function getPolicies() {
  return fetchJSON<
    Array<{
      id: string;
      name: string;
      domain: string;
      priority: number;
      is_active: boolean;
    }>
  >(`${POLICY_URL}/policies`);
}

export async function getApprovals(status: string = "pending") {
  return fetchJSON<
    Array<{ id: string; action_type: string; status: string; created_at: string }>
  >(`${POLICY_URL}/approvals?status=${status}`);
}

// ---- poQat Monitor API ----

export async function getSystemOverview() {
  return fetchJSON<{
    total_services: number;
    healthy_services: number;
    degraded_services: number;
    unhealthy_services: number;
    total_agents: number;
    healthy_agents: number;
    services: Array<{
      service_name: string;
      status: string;
      latency_ms: number | null;
      checked_at: string;
    }>;
    agents: Array<{
      agent_name: string;
      status: string;
      tasks_completed: number;
      tasks_failed: number;
      avg_confidence: number | null;
    }>;
  }>(`${POQAT_URL}/overview`);
}
