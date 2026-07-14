import { Section } from "../ui/Container";
import { Button, ctaToProps } from "../ui/Button";

type HeroProps = {
  title: string;
  subtitle?: string;
  cta_primary?: string | { label: string; href?: string };
  cta_secondary?: string | { label: string; href?: string };
  image?: { url?: string; alt?: string };
};

export function HeroSplit(props: HeroProps) {
  const ctaP = ctaToProps(props.cta_primary);
  const ctaS = ctaToProps(props.cta_secondary);
  return (
    <Section className="pt-24">
      <div className="grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">{props.title}</h1>
          {props.subtitle && <p className="mt-6 text-lg text-muted max-w-xl">{props.subtitle}</p>}
          <div className="mt-8 flex flex-wrap gap-3">
            {ctaP && <Button href={ctaP.href || "#contact"}>{ctaP.label}</Button>}
            {ctaS && <Button variant="secondary" href={ctaS.href || "#features"}>{ctaS.label}</Button>}
          </div>
        </div>
        {props.image?.url && (
          <div className="rounded-lg overflow-hidden border border-white/10">
            <img src={props.image.url} alt={props.image.alt || ""} className="w-full h-auto" />
          </div>
        )}
      </div>
    </Section>
  );
}

export function HeroCenter(props: HeroProps) {
  const ctaP = ctaToProps(props.cta_primary);
  const ctaS = ctaToProps(props.cta_secondary);
  return (
    <Section className="pt-24 text-center">
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight max-w-3xl mx-auto">{props.title}</h1>
      {props.subtitle && <p className="mt-6 text-lg text-muted max-w-2xl mx-auto">{props.subtitle}</p>}
      <div className="mt-8 flex flex-wrap gap-3 justify-center">
        {ctaP && <Button href={ctaP.href || "#contact"}>{ctaP.label}</Button>}
        {ctaS && <Button variant="secondary" href={ctaS.href || "#features"}>{ctaS.label}</Button>}
      </div>
    </Section>
  );
}
