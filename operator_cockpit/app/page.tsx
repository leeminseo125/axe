"use client";

import { useEffect, useState } from "react";
import StatCard from "@/components/shared/StatCard";
import StatusBadge from "@/components/shared/StatusBadge";
import {
  getAXEngineStats,
  getPOEStats,
  getSystemOverview,
} from "@/lib/api";

interface DashboardData {
  axengine: { failure_rate_1h: number; connectors: string[]; llm_providers: string[] } | null;
  poe: { events_24h: number; insights_24h: number; pending_decisions: number; executions_24h: number } | null;
  health: {
    total_services: number;
    healthy_services: number;
    services: Array<{ service_name: string; status: string; latency_ms: number | null }>;
  } | null;
  error: string | null;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>({
    axengine: null,
    poe: null,
    health: null,
    error: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [axengine, poe, health] = await Promise.allSettled([
          getAXEngineStats(),
          getPOEStats(),
          getSystemOverview(),
        ]);
        setData({
          axengine: axengine.status === "fulfilled" ? axengine.value : null,
          poe: poe.status === "fulfilled" ? poe.value : null,
          health: health.status === "fulfilled" ? health.value : null,
          error: null,
        });
      } catch (e: any) {
        setData((prev) => ({ ...prev, error: e.message }));
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-bold">Operator Cockpit</h2>
        <p className="text-gray-400 text-sm mt-1">
          AXEworks Foundation Engine - Real-time Operations Overview
        </p>
      </header>

      {data.error && (
        <div className="bg-axe-danger/10 border border-axe-danger/30 rounded-lg p-4 text-sm text-axe-danger">
          {data.error}
        </div>
      )}

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Services Health"
          value={
            data.health
              ? `${data.health.healthy_services}/${data.health.total_services}`
              : "--"
          }
          subtitle="Healthy / Total"
          color="success"
        />
        <StatCard
          title="Events (24h)"
          value={data.poe?.events_24h ?? "--"}
          subtitle="POE data events captured"
          color="accent"
        />
        <StatCard
          title="Pending Decisions"
          value={data.poe?.pending_decisions ?? "--"}
          subtitle="Awaiting approval or review"
          color="warning"
        />
        <StatCard
          title="Failure Rate (1h)"
          value={
            data.axengine
              ? `${(data.axengine.failure_rate_1h * 100).toFixed(1)}%`
              : "--"
          }
          subtitle="AXEngine execution failures"
          color={
            data.axengine && data.axengine.failure_rate_1h > 0.1
              ? "danger"
              : "success"
          }
        />
      </div>

      {/* Engine Status Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AXEngine Panel */}
        <div className="bg-axe-surface rounded-xl p-5">
          <h3 className="text-lg font-semibold mb-4">AXEngine (Internal Ops)</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">LLM Providers</span>
              <span>
                {data.axengine?.llm_providers.length
                  ? data.axengine.llm_providers.join(", ")
                  : "None available"}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Connectors</span>
              <span>{data.axengine?.connectors.join(", ") ?? "--"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Failure Rate</span>
              <span>
                {data.axengine
                  ? `${(data.axengine.failure_rate_1h * 100).toFixed(1)}%`
                  : "--"}
              </span>
            </div>
          </div>
        </div>

        {/* AXE_POE Panel */}
        <div className="bg-axe-surface rounded-xl p-5">
          <h3 className="text-lg font-semibold mb-4">AXE_POE (Product Ops)</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Events (24h)</span>
              <span>{data.poe?.events_24h ?? "--"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Insights (24h)</span>
              <span>{data.poe?.insights_24h ?? "--"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Executions (24h)</span>
              <span>{data.poe?.executions_24h ?? "--"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Pending Decisions</span>
              <span className="text-axe-warning font-medium">
                {data.poe?.pending_decisions ?? "--"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Service Health Table */}
      {data.health && data.health.services.length > 0 && (
        <div className="bg-axe-surface rounded-xl p-5">
          <h3 className="text-lg font-semibold mb-4">Service Health</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-left">
                  <th className="py-2 px-3 text-gray-400 text-xs uppercase">
                    Service
                  </th>
                  <th className="py-2 px-3 text-gray-400 text-xs uppercase">
                    Status
                  </th>
                  <th className="py-2 px-3 text-gray-400 text-xs uppercase">
                    Latency
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.health.services.map((svc) => (
                  <tr
                    key={svc.service_name}
                    className="border-b border-gray-800"
                  >
                    <td className="py-2 px-3 font-medium">
                      {svc.service_name}
                    </td>
                    <td className="py-2 px-3">
                      <StatusBadge status={svc.status} />
                    </td>
                    <td className="py-2 px-3 text-gray-400">
                      {svc.latency_ms ? `${svc.latency_ms.toFixed(0)}ms` : "--"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-axe-surface rounded w-64" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-axe-surface rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div className="h-48 bg-axe-surface rounded-xl" />
        <div className="h-48 bg-axe-surface rounded-xl" />
      </div>
    </div>
  );
}
