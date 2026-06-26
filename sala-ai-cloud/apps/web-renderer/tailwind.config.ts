import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // Toutes les couleurs sont pilotées par CSS variables injectées
      // depuis les design tokens du PageSchema (cf. lib/tokens.ts).
      colors: {
        primary:   "rgb(var(--color-primary) / <alpha-value>)",
        secondary: "rgb(var(--color-secondary) / <alpha-value>)",
        accent:    "rgb(var(--color-accent) / <alpha-value>)",
        bg:        "rgb(var(--color-bg) / <alpha-value>)",
        surface:   "rgb(var(--color-surface) / <alpha-value>)",
        text:      "rgb(var(--color-text) / <alpha-value>)",
        muted:     "rgb(var(--color-muted) / <alpha-value>)",
        success:   "rgb(var(--color-success) / <alpha-value>)",
        warning:   "rgb(var(--color-warning) / <alpha-value>)",
        danger:    "rgb(var(--color-danger) / <alpha-value>)",
      },
      fontFamily: {
        heading: ["var(--font-heading)", "system-ui", "sans-serif"],
        body:    ["var(--font-body)",    "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm:   "var(--radius-sm)",
        DEFAULT: "var(--radius-md)",
        lg:   "var(--radius-lg)",
        full: "var(--radius-full)",
      },
    },
  },
  plugins: [],
};

export default config;
