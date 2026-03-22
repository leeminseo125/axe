"use client";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "primary" | "success" | "warning" | "danger" | "accent";
}

const COLOR_MAP = {
  primary: "border-axe-primary",
  success: "border-axe-success",
  warning: "border-axe-warning",
  danger: "border-axe-danger",
  accent: "border-axe-accent",
};

export default function StatCard({ title, value, subtitle, color = "primary" }: StatCardProps) {
  return (
    <div className={`bg-axe-surface rounded-xl p-5 border-l-4 ${COLOR_MAP[color]}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}
