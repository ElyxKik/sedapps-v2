# Quick Start - SedApps

Démarrer rapidement avec SedApps (Flutter + Backend + Supabase).

## Option 1 : Développement local (SQLite)

### Backend

```bash
cd services/backend

# Installer les dépendances
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Lancer le backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Flutter

Dans un autre terminal :

```bash
cd apps/mobile

# Lancer Flutter (web)
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

## Option 2 : Avec Supabase (Production)

### 1. Créer un projet Supabase

1. Aller sur https://supabase.com
2. Créer un nouveau projet
3. Copier l'URL et la clé anon

### 2. Configurer le backend

```bash
cd services/backend

# Copier le template
cp .env.example .env

# Éditer .env avec vos credentials Supabase
# SEDAPPS_SUPABASE_URL=https://your-project.supabase.co
# SEDAPPS_SUPABASE_KEY=your-anon-key
```

### 3. Initialiser la base de données

```bash
# Installer les dépendances
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Créer les tables
python3 migrate.py

# Lancer le backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Lancer Flutter

```bash
cd apps/mobile

flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

## Option 3 : Docker Compose

```bash
# Lancer le backend avec SQLite
docker compose -f docker-compose.simple.yml up --build

# Dans un autre terminal, lancer Flutter
cd apps/mobile
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

## Endpoints principaux

- **Auth** : `POST /v1/auth/register`, `POST /v1/auth/login`
- **Projects** : `GET /v1/projects`, `POST /v1/projects`, `DELETE /v1/projects/{id}`
- **CMS** : `GET /v1/projects/{id}/articles`, `POST /v1/projects/{id}/articles`
- **Account** : `GET /v1/account`

## Troubleshooting

### Flutter ne se connecte pas au backend

```bash
# Vérifier que le backend est lancé
curl http://localhost:8000/docs

# Vérifier le CORE_API_BASE_URL
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

### Erreur de base de données

```bash
# Vérifier les credentials Supabase
cat services/backend/.env

# Réinitialiser les tables
python3 services/backend/migrate.py
```

### Port 8000 déjà utilisé

```bash
# Lancer sur un autre port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Mettre à jour Flutter
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8001 \
  --dart-define=MOCK_DATA=false
```

## Documentation complète

- Backend : `services/backend/README.md`
- Supabase : `SUPABASE_SETUP.md`
- Flutter + Supabase : `apps/mobile/SUPABASE_INTEGRATION.md`
