import type { Metadata } from "next";
import type { Page } from "@sedapps/page-schema";

export function buildMetadata(page: Page): Metadata {
  const m = page.meta;
  return {
    title: m.title,
    description: m.description,
    openGraph: {
      title: m.og?.title ?? m.title,
      description: m.og?.description ?? m.description,
      images: m.og?.image ? [m.og.image] : undefined,
    },
    twitter: {
      card: "summary_large_image",
      title: m.og?.title ?? m.title,
      description: m.og?.description ?? m.description,
    },
  };
}
