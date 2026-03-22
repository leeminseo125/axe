import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        axe: {
          primary: "#2563eb",
          secondary: "#7c3aed",
          dark: "#0f172a",
          surface: "#1e293b",
          accent: "#06b6d4",
          success: "#22c55e",
          warning: "#f59e0b",
          danger: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};

export default config;
