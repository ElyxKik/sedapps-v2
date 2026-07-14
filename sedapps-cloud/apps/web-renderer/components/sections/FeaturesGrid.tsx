import { Section } from "../ui/Container";

type Item = { title: string; desc?: string; icon?: string };

export function FeaturesGrid({
  title, subtitle, items = [], columns = 3,
}: { title?: string; subtitle?: string; items?: Item[]; columns?: 2 | 3 | 4 }) {
  const cols: Record<2 | 3 | 4, string> = {
    2: "sm:grid-cols-2",
    3: "sm:grid-cols-2 lg:grid-cols-3",
    4: "sm:grid-cols-2 lg:grid-cols-4",
  };
  return (
    <Section id="features">
      {(title || subtitle) && (
        <div className="text-center mb-12">
          {title && <h2 className="text-3xl sm:text-4xl">{title}</h2>}
          {subtitle && <p className="mt-3 text-muted max-w-2xl mx-auto">{subtitle}</p>}
        </div>
      )}
      <div className={`grid gap-6 ${cols[columns] || cols[3]}`}>
        {items.map((it, i) => (
          <div key={i} className="bg-surface border border-white/10 rounded-lg p-6 hover:border-white/20 transition">
            {it.icon && <div className="text-2xl mb-3 text-primary">{it.icon}</div>}
            <h3 className="text-lg font-semibold">{it.title}</h3>
            {it.desc && <p className="mt-2 text-muted text-sm">{it.desc}</p>}
          </div>
        ))}
      </div>
    </Section>
  );
}
