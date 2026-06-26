# Component System

This document defines the reusable component taxonomy used by the AI static-site generation pipeline and future drag & drop builder.

## Goals

- Standardize AI-generated HTML/CSS/JS sites.
- Keep visual and structural consistency across generated sites.
- Make sections reusable by the builder/editor.
- Support multi-page rendering.
- Avoid generic template-looking pages by combining components according to the business brief.
- Always use professional visual icons when useful for comprehension.
- Never use emojis unless the user explicitly asks for them.

## Folder Structure

```text
/components
  /layout
  /hero
  /marketing
  /social-proof
  /pricing
  /media
  /blog
  /contact
  /faq
  /ecommerce
  /restaurant
  /cta
  /ui
  /builder
  /seo
```

## Component Categories

### Layout

- Container
- Section
- Grid
- Stack
- Spacer
- Divider
- Header
- Navbar
- MobileMenu
- Breadcrumb
- Footer

### Hero

- HeroCentered
- HeroSplit
- HeroVideo
- HeroImage
- HeroMinimal
- HeroWithForm
- HeroSlider

### Business / Marketing

- FeaturesGrid
- FeatureCard
- ServicesList
- ServiceCard
- StatsCounter
- Timeline
- ProcessSteps
- MissionVision
- WhyChooseUs

### Social Proof

- Testimonials
- TestimonialsCarousel
- ReviewCard
- LogoCloud
- CaseStudies
- TrustedBy

### Pricing

- PricingTable
- PricingCard
- ComparisonTable
- PricingToggle
- FeatureComparison

### Media

- Gallery
- GalleryGrid
- ImageCard
- VideoSection
- Lightbox
- PortfolioGrid

### Blog / CMS

- BlogGrid
- BlogList
- BlogCard
- FeaturedPost
- BlogPost
- ArticleHeader
- ArticleContent
- AuthorBox
- RelatedPosts
- BlogSidebar
- BlogCategories
- BlogTags
- BlogSearch
- Pagination

### Contact

- ContactForm
- NewsletterForm
- QuoteForm
- ReservationForm
- ContactInfo
- MapSection
- OpeningHours

### Support

- FAQ
- FAQAccordion
- HelpCenter
- SupportCard

### E-commerce

- ProductsGrid
- ProductCard
- ProductDetails
- CartDrawer
- CheckoutForm
- OrderSummary

### Restaurant / Hotel

- MenuSection
- MenuCard
- ChefSection
- RoomsGrid
- BookingCTA

### CTA

- CTABanner
- CTASection
- CTAInline
- DownloadAppCTA

### UI Base

- Button
- IconButton
- Heading
- Paragraph
- Badge
- Card
- InfoCard
- Input
- Textarea
- Select
- Checkbox

### Builder

- SectionRenderer
- ComponentRegistry
- ThemeProvider
- StyleManager
- PageRenderer
- DragHandle
- DropZone

### SEO / Performance

- SEOHead
- StructuredData
- CookieBanner
- ConsentManager
- LazyImage

### Responsive

- DesktopOnly
- MobileOnly
- TabletView
- ResponsiveGrid

## MVP Components

The first production-ready component set should prioritize:

- Header
- Footer
- Hero
- FeaturesGrid
- ServicesList
- Testimonials
- PricingTable
- FAQ
- Gallery
- ContactForm
- BlogCard
- BlogPost
- CTASection
- SectionRenderer

## Section Metadata Contract

Each generated section should expose metadata that can be reused by the builder:

```json
{
  "id": "hero",
  "component": "HeroSplit",
  "title": "Main headline",
  "content": "Short summary of the section",
  "enabled": true
}
```

## Static Generation Contract

The AI generation must be multi-step and multi-page:

1. `SitePlannerAgent` decides the sitemap, navigation, page goals and component plan.
2. `StaticPageBuilderAgent` generates one HTML page at a time.
3. `AnimationDirectorAgent` chooses controlled animation presets and timings.
4. The workflow assembles shared `styles.css` and `script.js`.
5. The deploy service publishes the generated static files directly.

The AI must not generate the entire website in one single LLM response.

The final workflow output must contain deployable files:

```json
{
  "files": [
    { "path": "index.html", "content": "<!doctype html>..." },
    { "path": "services.html", "content": "<!doctype html>..." },
    { "path": "about.html", "content": "<!doctype html>..." },
    { "path": "contact.html", "content": "<!doctype html>..." },
    { "path": "styles.css", "content": "..." },
    { "path": "script.js", "content": "..." }
  ],
  "design_tokens": {},
  "sections": []
}
```

The deploy service then publishes these files directly without using the JSON renderer.

## Animation Engine

The AI must not freely invent animations. It must choose from a controlled animation library.

### Animation Stack

- CSS transitions for simple interactions.
- `IntersectionObserver` for scroll-triggered entry animations.
- Optional GSAP can be added later for advanced timeline animations, but static generation defaults to zero external dependency.

### Allowed Presets

Entry:

- fade-in
- fade-up
- fade-down
- fade-left
- fade-right
- zoom-in
- scale-in

Hover:

- lift-hover
- glow-hover
- underline-slide
- button-expand

Scroll:

- parallax
- sticky-reveal
- scroll-progress
- stagger-children

Micro-interactions:

- accordion-open
- modal-pop
- toast-slide
- menu-morph

Background:

- gradient-shift
- mesh-animation
- floating-shapes

### Motion Styles

- luxury
- startup
- creative
- corporate
- editorial
- minimal

### Motion Levels

- minimal
- medium
- advanced

### Animation Contract

```json
{
  "motion_style": "luxury",
  "motion_level": "medium",
  "use_gsap": false,
  "assignments": [
    {
      "page_path": "index.html",
      "section_id": "hero",
      "component": "HeroSplit",
      "selector": "#hero",
      "animation": {
        "enter": "fade-up",
        "hover": null,
        "scroll": null,
        "duration": 0.8,
        "delay": 0.1,
        "stagger": 0
      }
    }
  ]
}
```

### Performance Rules

- Animate only `transform` and `opacity` by default.
- Avoid animating `width`, `height`, `top`, `left`.
- Keep mobile animations lighter.
- Respect `prefers-reduced-motion`.
- Use animations to guide attention and conversion, not as decoration everywhere.
