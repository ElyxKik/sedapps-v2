# Architecture SedApps Cloud

Vue d'ensemble de l'architecture de la plateforme SaaS multi-tenant.

## Stack Technique

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Web/Mobile                       │
│  (Dashboard, Projects, CMS, Chat, Account, Onboarding,     │
│   Editor, Agents IA, Crédits, Publish)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         │ JWT Bearer Token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Core API (FastAPI)                             │
│  Auth, Projects, CMS, Jobs, Credits, Preview,              │
│  Chat IA, Editor (patch/undo), Download, Deploy            │
└──────────────┬──────────────────────────┬───────────────────┘
               │ SQL / SQLAlchemy         │ HTTP (internal token)
               ▼                          ▼
┌──────────────────────┐    ┌─────────────────────────────────┐
│  PostgreSQL 16       │    │  AI Orchestrator (FastAPI+Celery)│
│  (RLS multi-tenant)  │    │  12+ agents IA (DeepSeek V4)     │
│  Redis 7             │    │  Workflow: designer → copywriter │
│                      │    │  → planner → builder → QA        │
│                      │    │  → brand_compliance → uniqueness │
└──────────────────────┘    └──────────────┬──────────────────┘
                                           │ HTTP (internal token)
                                           ▼
                            ┌─────────────────────────────────┐
                            │  Deploy Service (FastAPI+Celery)│
                            │  Build static → Upload S3 OVH   │
                            │  → DNS CNAME → SSL              │
                            └─────────────────────────────────┘
```

## Services Docker

| Service | Port | Rôle |
|---------|------|------|
| `core-api` | 8000 | Auth, projets, CMS, jobs, crédits, preview, chat IA, editor |
| `ai-orchestrator` | 8001 | API orchestration + endpoints workflows |
| `ai-worker` | — | Celery worker (génération IA asynchrone) |
| `deploy-service` | 8002 | API déploiement |
| `deploy-worker` | — | Celery worker (build + upload + DNS) |
| `inbox-service` | 8003 | Réception formulaires de contact |
| `analytics-service` | 8004 | Tracking visiteurs / events |
| `flower` | 5555 | Monitoring Celery |
| `postgres` | 5432 | DB principale (RLS multi-tenant) |
| `redis` | 6379 | Broker Celery + cache |

## Flux de données

### Authentification
```
Flutter Login → Core API /v1/auth/login → JWT (access 15min + refresh 30j)
```

### Création de projet + Onboarding
```
Flutter → POST /v1/projects → DB
Flutter → POST /v1/projects/{id}/onboarding → brief stocké en JSONB
```

### Génération IA
```
Flutter → POST /v1/projects/{id}/generate
  → Core API crée AiJob (queued)
  → HTTP vers AI Orchestrator /v1/workflows/site-generation
  → Celery ai-worker exécute le workflow :
      1. DesignerAgent (palette, typo, logo)
      2. [Premium] StrategyDirectorAgent + UXArchitectAgent
      3. CopywriterAgent + SEOAgent + FormBuilderAgent + CMSBuilderAgent (parallèle)
      4. SitePlannerAgent (structure pages)
      5. StaticPageBuilderAgent × N pages (parallèle, retry si manquantes)
      6. AnimationDirectorAgent
      7. AnalyticsSetupAgent
      8. [Optionnel] BlogWriterAgent
      9. QAAgent (audit HTML)
      10. [Premium] PremiumQAAgent + RefinementAgent
      11. BrandCompliance validator (couleurs, logo, police, secteur)
      12. UniquenessScore validator (sections, variété, placeholders)
  → Callback Core API /v1/internal/jobs/{id}/complete
  → SiteVersion créée en DB (page_schema + design_tokens + seo)
```

### Édition de site
```
Flutter Editor → POST /v1/projects/{id}/patch_element (ops sur élément HTML)
Flutter Editor → POST /v1/projects/{id}/undo (annuler dernière modif)
Flutter Editor → POST /v1/projects/{id}/edit_chat (IA génère des ops)
```

### Chat IA
```
Flutter Chat → POST /v1/projects/{id}/chat → DeepSeek → réponse contextuelle
```

### Déploiement
```
Flutter → POST /v1/projects/{id}/deploy
  → Core API crée Deployment (queued)
  → HTTP vers Deploy Service /v1/deployments/site
  → Celery deploy-worker :
      1. Préparation workspace (static files ou renderer)
      2. Build (npm install + npm run build) ou copie directe
      3. Upload S3 OVH Object Storage
      4. Configuration DNS CNAME (si sous-domaine .sedapps.cloud)
      5. Callback Core API /v1/internal/deployments/{id}
```

### Preview
```
Flutter → GET /v1/p/{slug}/index.html → rendu HTML depuis SiteVersion
```

### Crédits IA
```
Flutter → GET /v1/credits/wallet → solde, quota, plan
Flutter → POST /v1/credits/estimate → estimation coût génération
  → Core API réserve crédits avant génération
  → Consomme/rembourse après completion (tokens réels)
```

## Modèles de données principaux

- **User** — utilisateurs (email, password_hash, name)
- **Organization** — tenant (isolation RLS)
- **Project** — projets (name, slug, sector, brief JSONB, design_tokens JSONB)
- **SiteVersion** — versions générées (page_schema JSONB, seo, design_tokens)
- **AiJob** — jobs de génération (status, input, output, tokens, cost)
- **AgentRun** — exécution agent (agent_name, model, tokens, output, warnings)
- **Deployment** — déploiements (status, domain, url)
- **Article** — articles CMS
- **CreditWallet** — portefeuille de crédits IA
- **CreditTransaction** — historique transactions crédits

## Sécurité

- **JWT** (access 15min + refresh 30j) avec rotation
- **RLS PostgreSQL** multi-tenant (chaque query set `tenant_id`)
- **Internal token** entre services (X-Internal-Token header)
- **CORS** configurable + regex localhost
- **Validation Pydantic** sur tous les inputs
- **SQLAlchemy ORM** (protection injection)

## Déploiement

### Local (Docker)
```bash
cp .env.example .env
make up        # postgres + redis + tous les services
make migrate   # migrations DB
make seed      # user demo + org
```

### Production
```bash
# Configurer .env avec credentials production
docker compose up -d --build
```

## Qualité de génération

Le workflow intègre trois validators déterministes post-génération :

1. **QAAgent** — audit structurel HTML (title, meta, H1, header/footer, viewport, liens internes, alt images, placeholders, formulaire contact)
2. **BrandCompliance** — vérifie que primary_color, secondary_color, logo_url, font_style, business_name et sector sont présents dans le HTML généré
3. **UniquenessScore** — évalue le nombre de sections, la variété des types (hero, features, testimonials, etc.), l'absence de placeholders, la diversité entre pages

Si le QA score est sous le seuil (70 standard / 85 premium), une passe de RefinementAgent est exécutée puis le QA est rejoué.

## Observabilité

- **AgentRun** : input/output/tokens/warnings par agent
- **Brand compliance** : score 0-100 sur respect des couleurs/logo/police
- **Uniqueness score** : score 0-100 sur la variété structurelle
- **QA score** : audit HTML (title, meta, H1, liens, alt, placeholders)
- **Flower** : monitoring Celery temps réel
- **Swagger UI** : `/docs` sur chaque service


## Notes

- L'IA utilise **DeepSeek V4** (Pro pour la génération, Flash pour l'édition ciblée)
- Les déploiements utilisent **OVH Object Storage (S3)** + DNS CNAME automatique
- Le renderer Astro est disponible en alternative (mode `astro` vs `static_classic`)
- Les fallbacks sectoriels génèrent du HTML unique par secteur (14 secteurs)
- Le système de crédits IA contrôle l'usage et les coûts
