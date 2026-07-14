# Architecture SedApps

Vue d'ensemble de l'architecture de l'application.

## Stack Technique

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Web/Mobile                       │
│  (Dashboard, Projects, CMS, Chat, Account, Onboarding)     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         │ JWT Bearer Token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                            │
│  (Auth, Projects, CMS, Jobs, Deployment, AI Simulation)    │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
                         │ SQLAlchemy ORM
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            PostgreSQL / Supabase / SQLite                   │
│  (Users, Projects, Articles, Jobs, Forms, Comments, Media) │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### Frontend (Flutter)

**Pages principales** :
- `DashboardPage` - Statistiques et projets récents
- `ProjectsPage` - Liste des projets avec CRUD
- `ProjectDetailPage` - Détail projet avec modals (Chat, Aperçu, CMS, etc.)
- `CMSPage` - Gestion des articles
- `AccountPage` - Profil utilisateur
- `LoginPage` - Authentification
- `OnboardingPage` - Wizard de création de projet

**State Management** :
- Riverpod pour la gestion d'état
- `ApiClient` pour les appels HTTP
- `ProjectWorkspaceState` pour l'état global du projet

### Backend (FastAPI)

**Routes principales** :
- `/v1/auth/*` - Authentification (register, login)
- `/v1/account` - Infos utilisateur
- `/v1/projects/*` - CRUD projets
- `/v1/projects/{id}/articles/*` - CRUD articles
- `/v1/projects/{id}/generate` - Génération IA
- `/v1/projects/{id}/deploy` - Déploiement
- `/v1/jobs/{id}` - Statut des jobs

**Modèles** :
- `User` - Utilisateurs
- `Project` - Projets
- `Article` - Articles CMS
- `AiJob` - Jobs de génération
- `FormSubmission` - Soumissions de formulaires
- `Comment` - Commentaires
- `Media` - Médias

### Base de données

**Schéma** :
```
users
├── id (PK)
├── email (UNIQUE)
├── hashed_password
├── name
├── organization
└── created_at

projects
├── id (PK)
├── user_id (FK)
├── name
├── sector
├── status (draft, published)
├── domain
└── created_at

articles
├── id (PK)
├── project_id (FK)
├── title
├── markdown
├── status (draft, published)
└── created_at

ai_jobs
├── id (PK)
├── project_id (FK)
├── status (queued, processing, completed, failed)
├── payload (JSON)
└── created_at

form_submissions
├── id (PK)
├── project_id (FK)
├── data (JSON)
└── created_at

comments
├── id (PK)
├── project_id (FK)
├── user_id (FK)
├── content
└── created_at

media
├── id (PK)
├── project_id (FK)
├── url
├── type
└── created_at
```

## Flux de données

### Authentification
```
Flutter Login → Backend /v1/auth/login → JWT Token → TokenStore
```

### Création de projet
```
Flutter Form → Backend /v1/projects → DB Insert → Return Project
```

### Génération IA
```
Flutter Onboarding → Backend /v1/projects/{id}/generate → AI Simulation → Job Created
Flutter Chat → Backend /v1/jobs/{id} → Return Agents → Display Chat
```

### CMS
```
Flutter CMS → Backend /v1/projects/{id}/articles → CRUD Articles → DB
```

## Sécurité

- **JWT Bearer Token** pour l'authentification
- **Hachage bcrypt** pour les mots de passe
- **CORS** configuré pour les domaines autorisés
- **Validation Pydantic** pour tous les inputs
- **SQL Injection** protégé par SQLAlchemy ORM

## Déploiement

### Local (SQLite)
```bash
uvicorn app.main:app --reload
```

### Production (Supabase)
```bash
# Configurer .env avec Supabase credentials
python migrate.py
uvicorn app.main:app
```

### Docker
```bash
docker compose -f docker-compose.simple.yml up --build
```

## Performance

- **Connection Pooling** : SQLAlchemy pool management
- **Caching** : Riverpod providers
- **Lazy Loading** : FutureBuilder pour les données asynchrones
- **Pagination** : À implémenter pour les listes longues

## Monitoring

- **Logs** : FastAPI logging
- **Errors** : Sentry (optionnel)
- **Database** : Supabase Studio
- **API** : Swagger UI à `/docs`

## Extensibilité

- Ajouter de nouveaux endpoints dans `app/main.py`
- Ajouter de nouveaux modèles dans `app/models.py`
- Ajouter de nouvelles pages Flutter dans `lib/src/features/`
- Ajouter de nouveaux providers Riverpod dans les pages

## Notes

- L'IA est simulée localement (pas d'appels externes)
- Les déploiements sont simulés (pas d'hébergement réel)
- Supabase est optionnel (SQLite fonctionne en local)
- Tous les endpoints sont documentés dans Swagger `/docs`
