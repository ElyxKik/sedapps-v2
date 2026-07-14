import { Section } from "../ui/Container";
import { Button } from "../ui/Button";

type Plan = {
  name: string; price: string; period?: string;
  features?: string[]; cta?: string; highlighted?: boolean;
};

export function PricingTable({
  title, plans = [],
}: { title?: string; plans?: Plan[] }) {
  return (
    <Section id="pricing">
      {title && <h2 className="text-3xl sm:text-4xl text-center mb-12">{title}</h2>}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((p, i) => (
          <div
            key={i}
            className={`rounded-lg p-6 border ${
              p.highlighted ? "border-primary bg-primary/5" : "border-white/10 bg-surface"
            }`}
          >
            <h3 className="text-lg font-semibold">{p.name}</h3>
            <div className="mt-3">
              <span className="text-4xl font-bold">{p.price}</span>
              {p.period && <span className="text-muted ml-1">/{p.period}</span>}
            </div>
            <ul className="mt-6 space-y-2 text-sm text-muted">
              {(p.features || []).map((f, j) => (
                <li key={j}>• {f}</li>
              ))}
            </ul>
            <div className="mt-6">
              <Button variant={p.highlighted ? "primary" : "secondary"} href="#contact">
                {p.cta || "Choisir"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}
