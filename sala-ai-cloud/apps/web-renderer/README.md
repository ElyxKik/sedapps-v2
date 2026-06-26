# @sedapps/web-renderer

Template Next.js 14 (App Router, SSG) qui consomme un **PageSchema JSON** et
produit un site statique exportable, prêt à uploader sur OVH Object Storage.

## Architecture

```
content/
  site.json           ← injecté par le deploy-service (PageSchema + tokens + articles)
  site.example.json   ← fallback de dev
app/
  layout.tsx          ← Header + Footer + injection design tokens (CSS vars) + Google Fonts
  page.tsx            ← /  (home)
  [slug]/page.tsx     ← /:slug/  (autres pages générées statiquement)
  blog/[slug]/page.tsx← /blog/:slug/
  sitemap.ts robots.ts
components/
  SectionRegistry.tsx ← mapping type -> composant React
  sections/           ← 11 composants (hero, features, pricing, faq, blog…)
lib/
  content.ts          ← parse + valide via Zod (@sedapps/page-schema)
  tokens.ts           ← convertit design tokens en CSS variables
  markdown.ts         ← rendu Markdown sanitizé (DOMPurify)
  seo.ts              ← generateMetadata helpers
```

## Dev local

```bash
# 1. installer (depuis la racine du monorepo)
cd ../../packages/page-schema && npm install
cd ../../apps/web-renderer && npm install

# 2. lancer
npm run dev

# 3. ouvrir http://localhost:3000
```

Le contenu affiché vient de `content/site.example.json` (une démo "Atelier Solène").

## Build statique (utilisé par le deploy-service)

```bash
npm run build
# → dossier `out/` à uploader vers OVH S3
```

## Comment le deploy-service injecte le contenu

1. Crée un dossier temporaire avec une copie du `web-renderer`.
2. Écrit le payload du job (sortie de l'orchestrateur) dans `content/site.json`.
3. Exécute `npm install && npm run build`.
4. Upload `out/*` vers le bucket S3 du projet client.
5. Pointe le DNS OVH `*.sedapps.cloud` vers le bucket + CDN.

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SITE_URL`      | URL absolue du site déployé (sitemap, OG) |
| `NEXT_PUBLIC_INBOX_URL`     | Base URL de l'inbox-service pour POST formulaires |
| `NEXT_PUBLIC_ANALYTICS_URL` | Base URL de l'analytics-service (tracker.js) |

## Sécurité

- Le `PageSchema` JSON est **validé par Zod** avant rendu → impossible
  d'injecter un type de section non whitelisté.
- Le Markdown passe par `remark-html` puis `DOMPurify` → pas de XSS possible
  via les outputs LLM.
- Aucun `dangerouslySetInnerHTML` avec contenu utilisateur non sanitizé.
