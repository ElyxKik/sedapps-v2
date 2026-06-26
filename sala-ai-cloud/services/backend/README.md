# SedApps Backend Simple

Backend mono-service pour tester rapidement l'application Flutter sans microservices.

## Stack

- FastAPI
- PostgreSQL (SQLite en local, Supabase en production)
- SQLAlchemy
- JWT Bearer Auth
- Simulation IA locale

## Configuration

### Variables d'environnement

Copier `.env.example` en `.env` et configurer :

```bash
cp .env.example .env
```

**Pour Supabase** :
1. Créer un projet Supabase sur https://supabase.com
2. Récupérer l'URL et la clé anon dans Settings > API
3. Configurer dans `.env` :
   ```
   SEDAPPS_SUPABASE_URL=https://your-project.supabase.co
   SEDAPPS_SUPABASE_KEY=your-supabase-anon-key
   ```

## Lancer en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Avec PostgreSQL local** :
```bash
# Installer PostgreSQL et créer la DB
createdb sedapps
# Configurer DATABASE_URL dans .env
SEDAPPS_DATABASE_URL=postgresql://postgres:password@localhost:5432/sedapps
```

## Lancer avec Docker Compose simple

Depuis la racine `sala-ai-cloud` :

```bash
docker compose -f docker-compose.simple.yml up --build
```

## Flutter

Lancer Flutter avec :

```bash
flutter run -d chrome --dart-define=CORE_API_BASE_URL=http://localhost:8000 --dart-define=MOCK_DATA=false
```

## Endpoints principaux

### Auth

- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/account`

### Projects

- `GET /v1/projects`
- `POST /v1/projects`
- `GET /v1/projects/{project_id}`
- `PATCH /v1/projects/{project_id}`
- `DELETE /v1/projects/{project_id}`
- `POST /v1/projects/{project_id}/onboarding`
- `POST /v1/projects/{project_id}/generate`
- `POST /v1/projects/{project_id}/deploy`

### Jobs

- `GET /v1/jobs/{job_id}`

### CMS

- `GET /v1/projects/{project_id}/articles`
- `POST /v1/projects/{project_id}/articles`
- `PATCH /v1/projects/{project_id}/articles/{article_id}`
- `DELETE /v1/projects/{project_id}/articles/{article_id}`

### Forms / Comments / Media

- `POST /v1/projects/{project_id}/forms/submissions`
- `GET /v1/projects/{project_id}/forms/submissions`
- `POST /v1/comments`
- `GET /v1/projects/{project_id}/comments`
- `PATCH /v1/comments/{comment_id}`
- `GET /v1/projects/{project_id}/media`
- `POST /v1/projects/{project_id}/media`

## Notes

- La génération IA est simulée immédiatement.
- Les agents sont retournés dans `GET /v1/jobs/{job_id}` pour alimenter le chat Flutter.
- Le déploiement est simulé et retourne une URL `https://{domain}`.
