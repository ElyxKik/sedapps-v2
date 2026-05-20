import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { Section } from "@/components/ui/Container";
import { getArticleBySlug, getArticles } from "@/lib/content";
import { renderMarkdown } from "@/lib/markdown";

export function generateStaticParams() {
  return getArticles().map((a) => ({ slug: a.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const a = getArticleBySlug(params.slug);
  if (!a) return {};
  return {
    title: a.seo?.title || a.title,
    description: a.seo?.meta_description || a.excerpt,
    openGraph: {
      title: a.seo?.title || a.title,
      description: a.seo?.meta_description || a.excerpt,
      images: a.seo?.og_image_url ? [a.seo.og_image_url] : a.cover_url ? [a.cover_url] : undefined,
      type: "article",
    },
  };
}

export default async function ArticlePage({ params }: { params: { slug: string } }) {
  const a = getArticleBySlug(params.slug);
  if (!a) notFound();
  const html = await renderMarkdown(a.content_md);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: a.title,
    image: a.cover_url ? [a.cover_url] : undefined,
    datePublished: a.published_at,
    description: a.excerpt,
  };
  return (
    <Section>
      <article className="max-w-3xl mx-auto">
        {a.cover_url && (
          <img src={a.cover_url} alt={a.title}
               className="w-full rounded-lg border border-white/10 mb-8" />
        )}
        <h1 className="text-3xl sm:text-4xl mb-4">{a.title}</h1>
        <p className="text-muted text-sm mb-8">{a.reading_time_min} min de lecture</p>
        <div className="prose-renderer" dangerouslySetInnerHTML={{ __html: html }} />
        <script type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      </article>
    </Section>
  );
}
