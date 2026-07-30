import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0f172a",
          muted: "#475569",
        },
        accent: {
          DEFAULT: "#0d9488",
          soft: "#ccfbf1",
        },
        paper: {
          DEFAULT: "#f8fafc",
          deep: "#e2e8f0",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
