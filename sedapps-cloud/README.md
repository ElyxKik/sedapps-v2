# SedApps Cloud

Plateforme SaaS multi-tenant qui génère, édite et héberge des sites web grâce à
une équipe d'agents IA spécialisés.

## Structure

```
sedapps-cloud/
├── apps/                  # (à venir) mobile Flutter, admin Next.js, web-renderer
├── services/
│   ├── core-api/          # FastAPI : auth, projets, CMS, billing
│   └── ai-orchestrator/   # FastAPI + Celery + 9 agents IA
├── packages/              # (à venir) shared-schemas, SDK Dart/TS
├── infra/                 # (à venir) k8s, terraform
├── docker-compose.yml     # dev local : postgres + redis + services
└── Makefile
```

## Lancement local

```bash
cp .env.example .env
# renseigner DEEPSEEK_API_KEY au minimum
make up        # build + démarre postgres, redis, core-api, ai-orchestrator, worker
make migrate   # applique les migrations
make seed      # crée un user demo + une org
make logs      # tail des logs
```

- core-api        : http://localhost:8000/docs
- ai-orchestrator : http://localhost:8001/docs
- flower (celery) : http://localhost:5555

## Stack

- **Backend** : FastAPI 0.115, SQLAlchemy 2.0, Alembic, Pydantic v2, Celery 5
- **DB**      : PostgreSQL 16 (RLS multi-tenant), Redis 7
- **IA**      : DeepSeek V4 (Pro / Flash), adapter OpenAI-compatible
- **Auth**    : JWT (access 15 min + refresh 30 j)
- **Storage** : OVH Object Storage S3 (à brancher)

## Conventions

- Toutes les tables métier portent `tenant_id` + RLS Postgres.
- Tout endpoint authentifié passe par `get_current_user` qui set
  `app.current_tenant` sur la connexion DB (isolation forte).
- Les agents IA renvoient un JSON strict validé par Pydantic.
