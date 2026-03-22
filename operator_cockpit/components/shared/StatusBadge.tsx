"use client";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const STATUS_COLORS: Record<string, string> = {
  healthy: "bg-axe-success/20 text-axe-success",
  running: "bg-axe-primary/20 text-axe-primary",
  completed: "bg-axe-success/20 text-axe-success",
  pending: "bg-gray-500/20 text-gray-400",
  planned: "bg-axe-accent/20 text-axe-accent",
  executing: "bg-axe-warning/20 text-axe-warning",
  failed: "bg-axe-danger/20 text-axe-danger",
  degraded: "bg-axe-warning/20 text-axe-warning",
  unhealthy: "bg-axe-danger/20 text-axe-danger",
  approved: "bg-axe-success/20 text-axe-success",
  proposed: "bg-axe-accent/20 text-axe-accent",
  blocked: "bg-axe-danger/20 text-axe-danger",
  awaiting_approval: "bg-axe-warning/20 text-axe-warning",
};

export default function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] || "bg-gray-500/20 text-gray-400";
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  return (
    <span className={`inline-block rounded-full font-medium ${colors} ${sizeClass}`}>
      {status}
    </span>
  );
}
