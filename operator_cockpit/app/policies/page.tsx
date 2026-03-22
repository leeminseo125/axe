"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/shared/StatusBadge";
import DataTable from "@/components/shared/DataTable";
import { getPolicies, getApprovals } from "@/lib/api";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, a] = await Promise.allSettled([
          getPolicies(),
          getApprovals(),
        ]);
        if (p.status === "fulfilled") setPolicies(p.value);
        if (a.status === "fulfilled") setApprovals(a.value);
      } catch {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const policyColumns = [
    { key: "name", header: "Policy Name" },
    { key: "domain", header: "Domain" },
    { key: "priority", header: "Priority" },
    {
      key: "is_active",
      header: "Status",
      render: (p: any) => (
        <StatusBadge status={p.is_active ? "healthy" : "degraded"} />
      ),
    },
  ];

  const approvalColumns = [
    { key: "action_type", header: "Action" },
    {
      key: "status",
      header: "Status",
      render: (a: any) => <StatusBadge status={a.status} />,
    },
    {
      key: "created_at",
      header: "Requested",
      render: (a: any) => new Date(a.created_at).toLocaleString(),
    },
  ];

  if (loading) return <div className="animate-pulse h-96 bg-axe-surface rounded-xl" />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Policy & Governance</h2>

      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Active Policies</h3>
        <DataTable columns={policyColumns} data={policies} emptyMessage="No policies configured" />
      </div>

      <div className="bg-axe-surface rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Pending Approvals</h3>
        <DataTable
          columns={approvalColumns}
          data={approvals}
          emptyMessage="No pending approvals"
        />
      </div>
    </div>
  );
}
