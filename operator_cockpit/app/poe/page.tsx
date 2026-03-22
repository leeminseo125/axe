"use client";

import { useEffect, useState } from "react";
import StatCard from "@/components/shared/StatCard";
import StatusBadge from "@/components/shared/StatusBadge";
import DataTable from "@/components/shared/DataTable";
import {
  getPOEStats,
  getInsights,
  getDecisions,
  approveDecision,
  runPipeline,
} from "@/lib/api";

export default function POEPage() {
  const [stats, setStats] = useState<any>(null);
  const [insights, setInsights] = useState<any[]>([]);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [s, i, d] = await Promise.allSettled([
        getPOEStats(),
        getInsights(),
        getDecisions(),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (i.status === "fulfilled") setInsights(i.value);
      if (d.status === "fulfilled") setDecisions(d.value);
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleRunPipeline() {
    setRunning(true);
    try {
      const result = await runPipeline(60);
      setPipelineResult(result);
      loadData();
    } catch {
    } finally {
      setRunning(false);
    }
  }

  async function handleApprove(id: string) {
    await approveDecision(id);
    loadData();
  }

  const insightColumns = [
    { key: "insight_type", header: "Type" },
    {
      key: "severity",
      header: "Severity",
      render: (i: any) => <StatusBadge status={i.severity} />,
    },
    { key: "summary", header: "Summary" },
    {
      key: "created_at",
      header: "Time",
      render: (i: any) => new Date(i.created_at).toLocaleTimeString(),
    },
  ];

  const decisionColumns = [
    { key: "recommended_action", header: "Action" },
    {
      key: "confidence",
      header: "Confidence",
      render: (d: any) => (
        <span className={d.confidence >= 0.8 ? "text-axe-success" : "text-axe-warning"}>
          {(d.confidence * 100).toFixed(0)}%
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (d: any) => <StatusBadge status={d.status} />,
    },
    {
      key: "actions",
      header: "Actions",
      render: (d: any) =>
        d.status === "awaiting_approval" || d.status === "proposed" ? (
          <button
            onClick={() => handleApprove(d.id)}
            className="text-xs bg-axe-success/20 text-axe-success px-3 py-1 rounded hover:bg-axe-success/30"
          >
            Approve
          </button>
        ) : null,
    },
  ];

  if (loading) return <div className="animate-pulse h-96 bg-axe-surface rounded-xl" />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">AXE_POE - Product Operations</h2>
          <p className="text-gray-400 text-sm">
            Analyze - Decide - Execute - Learn Pipeline
          </p>
        </div>
        <button
          onClick={handleRunPipeline}
          disabled={running}
          className="bg-axe-secondary px-6 py-2 rounded-lg text-sm font-medium hover:bg-axe-secondary/80 disabled:opacity-50"
        >
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      {/* Pipeline Result */}
      {pipelineResult && (
        <div className="bg-axe-accent/10 border border-axe-accent/30 rounded-lg p-4 text-sm">
          Pipeline completed: {pipelineResult.insights_generated} insights,{" "}
          {pipelineResult.decisions_made} decisions,{" "}
          {pipelineResult.executions_run} executions,{" "}
          {pipelineResult.feedbacks_recorded} feedbacks
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Events (24h)" value={stats?.events_24h ?? 0} color="accent" />
        <StatCard title="Insights (24h)" value={stats?.insights_24h ?? 0} color="primary" />
        <StatCard
          title="Pending Decisions"
          value={stats?.pending_decisions ?? 0}
          color="warning"
        />
        <StatCard
          title="Executions (24h)"
          value={stats?.executions_24h ?? 0}
          color="success"
        />
      </div>

      {/* Insights Table */}
      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Recent Insights</h3>
        <DataTable columns={insightColumns} data={insights} emptyMessage="No insights yet" />
      </div>

      {/* Decisions Table */}
      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Decisions</h3>
        <DataTable columns={decisionColumns} data={decisions} emptyMessage="No decisions yet" />
      </div>
    </div>
  );
}
