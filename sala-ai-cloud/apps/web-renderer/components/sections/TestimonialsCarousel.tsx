import { Section } from "../ui/Container";

type Item = { author: string; role?: string; quote: string; avatar?: string };

export function TestimonialsCarousel({
  title, items = [],
}: { title?: string; items?: Item[] }) {
  return (
    <Section id="testimonials">
      {title && <h2 className="text-3xl sm:text-4xl text-center mb-12">{title}</h2>}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map((t, i) => (
          <figure key={i} className="bg-surface border border-white/10 rounded-lg p-6">
            <blockquote className="text-muted italic">&ldquo;{t.quote}&rdquo;</blockquote>
            <figcaption className="mt-4 flex items-center gap-3">
              {t.avatar && <img src={t.avatar} alt={t.author} className="w-10 h-10 rounded-full" />}
              <div>
                <div className="font-semibold">{t.author}</div>
                {t.role && <div className="text-xs text-muted">{t.role}</div>}
              </div>
            </figcaption>
          </figure>
        ))}
      </div>
    </Section>
  );
}
