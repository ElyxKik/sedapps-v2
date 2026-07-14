import { Section } from "../ui/Container";
import { Button, ctaToProps } from "../ui/Button";

export function CTABanner({
  title, subtitle, cta,
}: {
  title: string;
  subtitle?: string;
  cta?: string | { label: string; href?: string };
}) {
  const c = ctaToProps(cta);
  return (
    <Section className="py-16">
      <div className="bg-gradient-to-br from-primary/20 to-secondary/20 border border-primary/30 rounded-lg p-10 text-center">
        <h2 className="text-2xl sm:text-3xl">{title}</h2>
        {subtitle && <p className="mt-3 text-muted max-w-xl mx-auto">{subtitle}</p>}
        {c && (
          <div className="mt-6">
            <Button href={c.href || "#contact"}>{c.label}</Button>
          </div>
        )}
      </div>
    </Section>
  );
}
