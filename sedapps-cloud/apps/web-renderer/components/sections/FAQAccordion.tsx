import { Section } from "../ui/Container";

export function FAQAccordion({
  title, items = [],
}: { title?: string; items?: { q: string; a: string }[] }) {
  // Server-rendered — utilise <details>/<summary>, pas de JS requis.
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((it) => ({
      "@type": "Question",
      name: it.q,
      acceptedAnswer: { "@type": "Answer", text: it.a },
    })),
  };
  return (
    <Section id="faq">
      {title && <h2 className="text-3xl sm:text-4xl text-center mb-12">{title}</h2>}
      <div className="max-w-3xl mx-auto space-y-3">
        {items.map((it, i) => (
          <details
            key={i}
            className="group bg-surface border border-white/10 rounded-lg p-5 open:border-white/20"
          >
            <summary className="cursor-pointer font-semibold flex justify-between items-center">
              {it.q}
              <span className="text-muted group-open:rotate-45 transition">+</span>
            </summary>
            <p className="mt-3 text-muted whitespace-pre-line">{it.a}</p>
          </details>
        ))}
      </div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </Section>
  );
}
