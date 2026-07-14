import type { MetadataRoute } from "next";
import { getAllPages, getArticles } from "@/lib/content";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_SITE_URL || "https://example.com";
  const pages = getAllPages().map((p) => ({
    url: p.meta.slug === "home" ? `${base}/` : `${base}/${p.meta.slug}/`,
    changeFrequency: "weekly" as const,
    priority: p.meta.slug === "home" ? 1.0 : 0.7,
  }));
  const articles = getArticles().map((a) => ({
    url: `${base}/blog/${a.slug}/`,
    changeFrequency: "monthly" as const,
    priority: 0.6,
    lastModified: a.published_at,
  }));
  return [...pages, ...articles];
}
