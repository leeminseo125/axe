"use client";

import { useEffect, useState } from "react";
import StatCard from "@/components/shared/StatCard";
import StatusBadge from "@/components/shared/StatusBadge";
import DataTable from "@/components/shared/DataTable";
import {
  getGoals,
  createGoal,
  planGoal,
  getHITLStats,
  getConnectorsHealth,
} from "@/lib/api";

interface Goal {
  id: string;
  title: string;
  status: string;
  priority: number;
  created_at: string;
}

export default function AXEnginePage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [hitlStats, setHitlStats] = useState<any>(null);
  const [connectors, setConnectors] = useState<Record<string, boolean>>({});
  const [newGoal, setNewGoal] = useState({ title: "", description: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [g, h, c] = await Promise.allSettled([
        getGoals(),
        getHITLStats(),
        getConnectorsHealth(),
      ]);
      if (g.status === "fulfilled") setGoals(g.value);
      if (h.status === "fulfilled") setHitlStats(h.value);
      if (c.status === "fulfilled") setConnectors(c.value);
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!newGoal.title) return;
    await createGoal(newGoal);
    setNewGoal({ title: "", description: "" });
    loadData();
  }

  async function handlePlanGoal(goalId: string) {
    await planGoal(goalId);
    loadData();
  }

  const goalColumns = [
    { key: "title", header: "Goal" },
    {
      key: "status",
      header: "Status",
      render: (g: Goal) => <StatusBadge status={g.status} />,
    },
    { key: "priority", header: "Priority" },
    {
      key: "created_at",
      header: "Created",
      render: (g: Goal) => new Date(g.created_at).toLocaleDateString(),
    },
    {
      key: "actions",
      header: "Actions",
      render: (g: Goal) =>
        g.status === "pending" ? (
          <button
            onClick={() => handlePlanGoal(g.id)}
            className="text-xs bg-axe-primary px-3 py-1 rounded hover:bg-axe-primary/80"
          >
            Plan
          </button>
        ) : null,
    },
  ];

  if (loading) return <div className="animate-pulse h-96 bg-axe-surface rounded-xl" />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">AXEngine - Internal Operations</h2>

      {/* HITL & Connector Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="HITL Overrides"
          value={hitlStats?.total_overrides ?? 0}
          subtitle={`Threshold: ${hitlStats?.current_base_threshold ?? 0.8}`}
          color="warning"
        />
        <StatCard
          title="Active Connectors"
          value={Object.values(connectors).filter(Boolean).length}
          subtitle={`${Object.keys(connectors).length} configured`}
          color="accent"
        />
        <StatCard
          title="Total Goals"
          value={goals.length}
          subtitle={`${goals.filter((g) => g.status === "pending").length} pending`}
          color="primary"
        />
      </div>

      {/* Connector Health */}
      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Integration Connectors</h3>
        <div className="flex gap-4">
          {Object.entries(connectors).map(([name, healthy]) => (
            <div
              key={name}
              className="flex items-center gap-2 bg-axe-dark rounded-lg px-4 py-2"
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  healthy ? "bg-axe-success" : "bg-axe-danger"
                }`}
              />
              <span className="text-sm">{name.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Create Goal Form */}
      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Create Goal</h3>
        <form onSubmit={handleCreateGoal} className="flex gap-3">
          <input
            type="text"
            placeholder="Goal title..."
            value={newGoal.title}
            onChange={(e) =>
              setNewGoal((prev) => ({ ...prev, title: e.target.value }))
            }
            className="flex-1 bg-axe-dark border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-axe-primary"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newGoal.description}
            onChange={(e) =>
              setNewGoal((prev) => ({ ...prev, description: e.target.value }))
            }
            className="flex-1 bg-axe-dark border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-axe-primary"
          />
          <button
            type="submit"
            className="bg-axe-primary px-6 py-2 rounded-lg text-sm font-medium hover:bg-axe-primary/80"
          >
            Create
          </button>
        </form>
      </div>

      {/* Goals Table */}
      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Goals</h3>
        <DataTable columns={goalColumns} data={goals} emptyMessage="No goals created yet" />
      </div>
    </div>
  );
}
