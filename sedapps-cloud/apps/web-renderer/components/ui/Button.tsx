import type { ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";
type CtaProp = string | { label: string; href?: string } | undefined;

export function Button({
  children,
  href,
  variant = "primary",
  className = "",
}: {
  children: ReactNode;
  href?: string;
  variant?: Variant;
  className?: string;
}) {
  const base = "inline-flex items-center justify-center px-5 py-2.5 rounded-md font-semibold transition";
  const styles: Record<Variant, string> = {
    primary:
      "bg-primary text-white hover:opacity-90 shadow-[0_8px_24px_-8px_rgb(var(--color-primary)/0.6)]",
    secondary:
      "border border-white/15 text-text hover:bg-white/5",
    ghost: "text-text hover:bg-white/5",
  };
  const cls = `${base} ${styles[variant]} ${className}`;
  if (href) return <a href={href} className={cls}>{children}</a>;
  return <button className={cls}>{children}</button>;
}

export function ctaToProps(cta: CtaProp): { label: string; href?: string } | null {
  if (!cta) return null;
  if (typeof cta === "string") return { label: cta };
  return cta;
}
