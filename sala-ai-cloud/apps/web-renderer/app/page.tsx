import type { Metadata } from "next";
import { SectionRenderer } from "@/components/SectionRegistry";
import { getHomePage } from "@/lib/content";
import { buildMetadata } from "@/lib/seo";

export function generateMetadata(): Metadata {
  return buildMetadata(getHomePage());
}

export default function HomePage() {
  const page = getHomePage();
  return (
    <>
      {Object.keys(page.meta.schema_org || {}).length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(page.meta.schema_org) }}
        />
      )}
      {page.sections.map((s) => (
        <SectionRenderer key={s.id} section={s} />
      ))}
    </>
  );
}
