import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { SectionRenderer } from "@/components/SectionRegistry";
import { getAllPages, getPageBySlug } from "@/lib/content";
import { buildMetadata } from "@/lib/seo";

export function generateStaticParams() {
  return getAllPages()
    .filter((p) => p.meta.slug !== "home")
    .map((p) => ({ slug: p.meta.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const page = getPageBySlug(params.slug);
  return page ? buildMetadata(page) : {};
}

export default function DynamicPage({ params }: { params: { slug: string } }) {
  const page = getPageBySlug(params.slug);
  if (!page) notFound();
  return (
    <>
      {page.sections.map((s) => (
        <SectionRenderer key={s.id} section={s} />
      ))}
    </>
  );
}
