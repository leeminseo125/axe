import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AXEworks Operator Cockpit",
  description: "Foundation Engine Operations Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}

function Sidebar() {
  const navItems = [
    { href: "/", label: "Dashboard", icon: "grid" },
    { href: "/axengine", label: "AXEngine", icon: "cpu" },
    { href: "/poe", label: "AXE_POE", icon: "activity" },
    { href: "/policies", label: "Policies", icon: "shield" },
    { href: "/health", label: "System Health", icon: "heart" },
  ];

  return (
    <aside className="w-64 bg-axe-surface border-r border-gray-700 p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-axe-accent">AXEworks</h1>
        <p className="text-xs text-gray-400 mt-1">Operator Cockpit v1.0</p>
      </div>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            {item.label}
          </a>
        ))}
      </nav>
      <div className="mt-auto pt-4 border-t border-gray-700 text-xs text-gray-500">
        AXEworks Foundation Engine
      </div>
    </aside>
  );
}
