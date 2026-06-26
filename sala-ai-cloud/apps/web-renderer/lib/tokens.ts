/**
 * Convertit les design tokens en CSS variables RGB injectables dans <style>.
 * Tailwind les lit via la config (cf. tailwind.config.ts).
 */
import type { DesignTokens } from "@sedapps/page-schema";

function hexToRgb(hex: string): string {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const num = parseInt(full, 16);
  if (Number.isNaN(num)) return "0 0 0";
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `${r} ${g} ${b}`;
}

export function tokensToCss(t: DesignTokens): string {
  const p = t.palette;
  const lines: string[] = [
    `:root {`,
    `  --color-primary: ${hexToRgb(p.primary)};`,
    `  --color-secondary: ${hexToRgb(p.secondary ?? p.primary)};`,
    `  --color-accent: ${hexToRgb(p.accent ?? p.primary)};`,
    `  --color-bg: ${hexToRgb(p.bg)};`,
    `  --color-surface: ${hexToRgb(p.surface)};`,
    `  --color-text: ${hexToRgb(p.text)};`,
    `  --color-muted: ${hexToRgb(p.muted ?? "#94a3b8")};`,
    `  --color-success: ${hexToRgb(p.success ?? "#10b981")};`,
    `  --color-warning: ${hexToRgb(p.warning ?? "#f59e0b")};`,
    `  --color-danger: ${hexToRgb(p.danger ?? "#ef4444")};`,
    `  --font-heading: "${t.typography.heading}";`,
    `  --font-body: "${t.typography.body}";`,
    `  --radius-sm: ${t.radius.sm ?? "6px"};`,
    `  --radius-md: ${t.radius.md ?? "10px"};`,
    `  --radius-lg: ${t.radius.lg ?? "16px"};`,
    `  --radius-full: ${t.radius.full ?? "9999px"};`,
    `}`,
  ];
  return lines.join("\n");
}

export function googleFontsHref(t: DesignTokens): string {
  const fams = [t.typography.heading, t.typography.body]
    .filter((v, i, a) => v && a.indexOf(v) === i)
    .map((f) => `family=${f.replace(/ /g, "+")}:wght@400;600;700`)
    .join("&");
  return `https://fonts.googleapis.com/css2?${fams}&display=swap`;
}
