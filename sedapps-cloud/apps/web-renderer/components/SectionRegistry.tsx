import type { Section, SectionType } from "@sedapps/page-schema";

import { HeroSplit, HeroCenter } from "./sections/Hero";
import { FeaturesGrid } from "./sections/FeaturesGrid";
import { AboutSplit } from "./sections/AboutSplit";
import { TestimonialsCarousel } from "./sections/TestimonialsCarousel";
import { PricingTable } from "./sections/PricingTable";
import { FAQAccordion } from "./sections/FAQAccordion";
import { CTABanner } from "./sections/CTABanner";
import { FormContact } from "./sections/FormContact";
import { BlogIndex } from "./sections/BlogIndex";
import { Richtext } from "./sections/Richtext";
import { GalleryGrid } from "./sections/GalleryGrid";

const REGISTRY: Record<SectionType, (props: any) => JSX.Element> = {
  "hero.split":            HeroSplit,
  "hero.center":           HeroCenter,
  "features.grid":         FeaturesGrid,
  "about.split":           AboutSplit,
  "testimonials.carousel": TestimonialsCarousel,
  "pricing.table":         PricingTable,
  "faq.accordion":         FAQAccordion,
  "cta.banner":            CTABanner,
  "form.contact":          FormContact,
  "blog.index":            BlogIndex,
  "richtext":              Richtext,
  "gallery.grid":          GalleryGrid,
};

export function SectionRenderer({ section }: { section: Section }) {
  const Cmp = REGISTRY[section.type];
  if (!Cmp) return null;
  return <Cmp {...section.props} />;
}
