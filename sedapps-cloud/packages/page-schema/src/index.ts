/**
 * PageSchema — JSON normalisé produit par le FrontendGeneratorAgent
 * et consommé par le web-renderer Next.js.
 *
 * Toute mutation du schéma DOIT passer par Zod pour rejeter les payloads
 * invalides (couche de sécurité supplémentaire face aux outputs LLM).
 */
import { z } from "zod";

// ── Design tokens ────────────────────────────────────────────────────────────

export const PaletteSchema = z.object({
  primary:   z.string(),
  secondary: z.string().optional(),
  accent:    z.string().optional(),
  bg:        z.string(),
  surface:   z.string(),
  text:      z.string(),
  muted:     z.string().optional(),
  success:   z.string().optional(),
  warning:   z.string().optional(),
  danger:    z.string().optional(),
});

export const TypographySchema = z.object({
  heading: z.string(),
  body:    z.string(),
  scale: z.object({
    h1:    z.string(),
    h2:    z.string(),
    h3:    z.string(),
    body:  z.string(),
    small: z.string(),
  }),
});

export const DesignTokensSchema = z.object({
  palette:    PaletteSchema,
  typography: TypographySchema,
  spacing:    z.record(z.string()),
  radius:     z.record(z.string()),
  shadow:     z.record(z.string()).optional(),
  vibe:       z.string().optional(),
});

// ── Section primitives ───────────────────────────────────────────────────────

const Cta = z.object({
  label: z.string(),
  href:  z.string().optional(),
});

const AssetRef = z.object({
  url:  z.string().optional(),
  alt:  z.string().optional(),
});

// ── Sections (discriminated union by `type`) ─────────────────────────────────

export const HeroSplitProps = z.object({
  title:    z.string(),
  subtitle: z.string().optional(),
  cta_primary:   z.union([z.string(), Cta]).optional(),
  cta_secondary: z.union([z.string(), Cta]).optional(),
  image:    AssetRef.optional(),
});

export const HeroCenterProps = HeroSplitProps;

export const FeatureItem = z.object({
  title: z.string(),
  desc:  z.string().optional(),
  icon:  z.string().optional(),
});

export const FeaturesGridProps = z.object({
  title:    z.string().optional(),
  subtitle: z.string().optional(),
  items:    z.array(FeatureItem).default([]),
  columns:  z.union([z.literal(2), z.literal(3), z.literal(4)]).default(3),
});

export const AboutSplitProps = z.object({
  title: z.string(),
  body:  z.string(),
  image: AssetRef.optional(),
});

export const Testimonial = z.object({
  author: z.string(),
  role:   z.string().optional(),
  quote:  z.string(),
  avatar: z.string().optional(),
});
export const TestimonialsCarouselProps = z.object({
  title: z.string().optional(),
  items: z.array(Testimonial).default([]),
});

export const PricingPlan = z.object({
  name:     z.string(),
  price:    z.string(),
  period:   z.string().optional(),
  features: z.array(z.string()).default([]),
  cta:      z.string().default("Choisir"),
  highlighted: z.boolean().optional(),
});
export const PricingTableProps = z.object({
  title: z.string().optional(),
  plans: z.array(PricingPlan).default([]),
});

export const FAQItem = z.object({ q: z.string(), a: z.string() });
export const FAQAccordionProps = z.object({
  title: z.string().optional(),
  items: z.array(FAQItem).default([]),
});

export const CTABannerProps = z.object({
  title:    z.string(),
  subtitle: z.string().optional(),
  cta:      z.union([z.string(), Cta]).optional(),
});

export const FormContactProps = z.object({
  title:    z.string().optional(),
  subtitle: z.string().optional(),
  form_id:  z.string(),
  layout:   z.enum(["single", "split"]).default("split"),
});

export const BlogIndexProps = z.object({
  title:    z.string().optional(),
  style:    z.enum(["grid", "list", "magazine"]).default("grid"),
  per_page: z.number().int().positive().max(50).default(9),
});

export const RichtextProps = z.object({
  markdown: z.string(),
});

export const GalleryGridProps = z.object({
  title: z.string().optional(),
  items: z.array(AssetRef).default([]),
});

export const SectionSchema = z.discriminatedUnion("type", [
  z.object({ id: z.string(), type: z.literal("hero.split"),             props: HeroSplitProps }),
  z.object({ id: z.string(), type: z.literal("hero.center"),            props: HeroCenterProps }),
  z.object({ id: z.string(), type: z.literal("features.grid"),          props: FeaturesGridProps }),
  z.object({ id: z.string(), type: z.literal("about.split"),            props: AboutSplitProps }),
  z.object({ id: z.string(), type: z.literal("testimonials.carousel"),  props: TestimonialsCarouselProps }),
  z.object({ id: z.string(), type: z.literal("pricing.table"),          props: PricingTableProps }),
  z.object({ id: z.string(), type: z.literal("faq.accordion"),          props: FAQAccordionProps }),
  z.object({ id: z.string(), type: z.literal("cta.banner"),             props: CTABannerProps }),
  z.object({ id: z.string(), type: z.literal("form.contact"),           props: FormContactProps }),
  z.object({ id: z.string(), type: z.literal("blog.index"),             props: BlogIndexProps }),
  z.object({ id: z.string(), type: z.literal("richtext"),               props: RichtextProps }),
  z.object({ id: z.string(), type: z.literal("gallery.grid"),           props: GalleryGridProps }),
]);

export type Section = z.infer<typeof SectionSchema>;
export type SectionType = Section["type"];

// ── Page ────────────────────────────────────────────────────────────────────

export const PageMetaSchema = z.object({
  slug:        z.string(),
  title:       z.string(),
  description: z.string().default(""),
  og: z.object({
    title:       z.string().optional(),
    description: z.string().optional(),
    image:       z.string().optional(),
  }).default({}),
  schema_org: z.record(z.unknown()).default({}),
});

export const PageLayoutSchema = z.object({
  header_id: z.string().default("default"),
  footer_id: z.string().default("default"),
});

export const PageSchema = z.object({
  meta:     PageMetaSchema,
  layout:   PageLayoutSchema.default({ header_id: "default", footer_id: "default" }),
  sections: z.array(SectionSchema).default([]),
});

// ── Site ────────────────────────────────────────────────────────────────────

export const SiteSchema = z.object({
  pages: z.array(PageSchema).min(1),
});

export type Page = z.infer<typeof PageSchema>;
export type Site = z.infer<typeof SiteSchema>;
export type DesignTokens = z.infer<typeof DesignTokensSchema>;

// ── Article (CMS) ───────────────────────────────────────────────────────────

export const ArticleSeoSchema = z.object({
  title:            z.string().optional(),
  meta_description: z.string().optional(),
  keywords:         z.array(z.string()).default([]),
  og_image_url:     z.string().optional(),
  canonical:        z.string().optional(),
  noindex:          z.boolean().optional(),
});

export const ArticleSchema = z.object({
  slug:             z.string(),
  title:            z.string(),
  excerpt:          z.string().optional(),
  cover_url:        z.string().optional(),
  content_md:       z.string().default(""),
  published_at:     z.string().optional(),
  reading_time_min: z.number().int().nonnegative().default(1),
  seo:              ArticleSeoSchema.default({}),
});

export type Article = z.infer<typeof ArticleSchema>;

// ── Full payload from orchestrator ──────────────────────────────────────────

export const SitePayloadSchema = z.object({
  page_schema:   SiteSchema,
  design_tokens: DesignTokensSchema,
  seo: z.object({
    sitemap: z.object({ include: z.array(z.string()).default([]) }).default({ include: [] }),
    robots:  z.string().default("User-agent: *\nAllow: /"),
  }).default({ sitemap: { include: [] }, robots: "User-agent: *\nAllow: /" }),
  form: z.object({
    id:              z.string(),
    name:            z.string().default("Contact"),
    fields:          z.array(z.record(z.unknown())).default([]),
    submit_label:    z.string().default("Envoyer"),
    success_message: z.string().default("Merci !"),
  }).partial().optional(),
  analytics: z.object({
    tracker_id: z.string().optional(),
  }).partial().optional(),
  articles: z.array(ArticleSchema).default([]),
});

export type SitePayload = z.infer<typeof SitePayloadSchema>;
