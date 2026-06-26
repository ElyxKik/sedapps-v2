/**
 * Charge le payload du site (page_schema + design_tokens + articles…).
 *
 * Source : `content/site.json` (injecté par le deploy-service au moment du build,
 * ou présent en local pour le dev — un fallback `content/site.example.json` est
 * inclus dans le repo).
 */
import fs from "node:fs";
import path from "node:path";
import {
  SitePayloadSchema,
  type SitePayload,
  type Page,
} from "@sedapps/page-schema";

let cached: SitePayload | null = null;

function resolveContentFile(): string {
  const base = path.join(process.cwd(), "content");
  for (const name of ["site.json", "site.example.json"]) {
    const p = path.join(base, name);
    if (fs.existsSync(p)) return p;
  }
  throw new Error(
    "No content/site.json found. Run with example or provide one before `next build`.",
  );
}

export function getSitePayload(): SitePayload {
  if (cached) return cached;
  const file = resolveContentFile();
  const raw = JSON.parse(fs.readFileSync(file, "utf-8"));
  const parsed = SitePayloadSchema.safeParse(raw);
  if (!parsed.success) {
    console.error("Invalid site payload:", parsed.error.format());
    throw new Error("Invalid site payload — aborting build.");
  }
  cached = parsed.data;
  return cached;
}

export function getAllPages(): Page[] {
  return getSitePayload().page_schema.pages;
}

export function getPageBySlug(slug: string): Page | null {
  return getAllPages().find((p) => p.meta.slug === slug) ?? null;
}

export function getHomePage(): Page {
  const pages = getAllPages();
  return pages.find((p) => p.meta.slug === "home") ?? pages[0];
}

export function getArticles() {
  return getSitePayload().articles;
}

export function getArticleBySlug(slug: string) {
  return getArticles().find((a) => a.slug === slug) ?? null;
}
