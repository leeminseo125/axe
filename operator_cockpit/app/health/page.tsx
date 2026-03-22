"use client";

import { useEffect, useState } from "react";
import StatCard from "@/components/shared/StatCard";
import StatusBadge from "@/components/shared/StatusBadge";
import DataTable from "@/components/shared/DataTable";
import { getSystemOverview } from "@/lib/api";

export default function HealthPage() {
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSystemOverview();
        setOverview(data);
      } catch {
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const serviceColumns = [
    { key: "service_name", header: "Service" },
    {
      key: "status",
      header: "Status",
      render: (s: any) => <StatusBadge status={s.status} />,
    },
    {
      key: "latency_ms",
      header: "Latency",
      render: (s: any) =>
        s.latency_ms != null ? `${s.latency_ms.toFixed(0)}ms` : "--",
    },
    {
      key: "error_count",
      header: "Errors",
      render: (s: any) => (
        <span className={s.error_count > 0 ? "text-axe-danger" : ""}>
          {s.error_count ?? 0}
        </span>
      ),
    },
    {
      key: "checked_at",
      header: "Last Check",
      render: (s: any) => new Date(s.checked_at).toLocaleTimeString(),
    },
  ];

  const agentColumns = [
    { key: "agent_name", header: "Agent" },
    { key: "domain", header: "Domain" },
    {
      key: "status",
      header: "Status",
      render: (a: any) => <StatusBadge status={a.status} />,
    },
    { key: "tasks_completed", header: "Completed" },
    {
      key: "tasks_failed",
      header: "Failed",
      render: (a: any) => (
        <span className={a.tasks_failed > 0 ? "text-axe-danger" : ""}>
          {a.tasks_failed}
        </span>
      ),
    },
    {
      key: "avg_confidence",
      header: "Avg Confidence",
      render: (a: any) =>
        a.avg_confidence != null
          ? `${(a.avg_confidence * 100).toFixed(0)}%`
          : "--",
    },
  ];

  if (loading) return <div className="animate-pulse h-96 bg-axe-surface rounded-xl" />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">System Health (poQat)</h2>

      {overview && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Total Services"
              value={overview.total_services}
              color="primary"
            />
            <StatCard
              title="Healthy"
              value={overview.healthy_services}
              color="success"
            />
            <StatCard
              title="Degraded"
              value={overview.degraded_services}
              color="warning"
            />
            <StatCard
              title="Unhealthy"
              value={overview.unhealthy_services}
              color="danger"
            />
          </div>

          <div className="bg-axe-surface rounded-xl p-5">
            <h3 className="text-lg font-semibold mb-3">Services</h3>
            <DataTable
              columns={serviceColumns}
              data={overview.services}
              emptyMessage="No service data"
            />
          </div>

          <div className="bg-axe-surface rounded-xl p-5">
            <h3 className="text-lg font-semibold mb-3">Agents</h3>
            <DataTable
              columns={agentColumns}
              data={overview.agents}
              emptyMessage="No agent data"
            />
          </div>
        </>
      )}
    </div>
  );
}
