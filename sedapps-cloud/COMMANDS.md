# Commandes utiles

Référence rapide des commandes pour développer et déployer SedApps.

## Backend

### Installation et démarrage

```bash
cd services/backend

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -e .

# Lancer le backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer sur un autre port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Base de données

```bash
# Créer les tables
python3 migrate.py

# Accéder à la base SQLite
sqlite3 sedapps.db

# Vérifier les tables
.tables

# Quitter
.quit
```

### Tests

```bash
# Vérifier la syntaxe Python
python3 -m py_compile app/*.py migrate.py

# Tester un endpoint
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Voir la documentation API
open http://localhost:8000/docs
```

### Docker

```bash
# Construire l'image
docker build -t sedapps-backend ./services/backend

# Lancer le conteneur
docker run -p 8000:8000 sedapps-backend

# Avec docker-compose
docker compose -f docker-compose.simple.yml up --build
docker compose -f docker-compose.simple.yml down
docker compose -f docker-compose.simple.yml logs -f backend
```

## Flutter

### Installation et démarrage

```bash
cd apps/mobile

# Installer les dépendances
flutter pub get

# Lancer sur web
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false

# Lancer sur un autre port
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8001 \
  --dart-define=MOCK_DATA=false

# Lancer en mode release
flutter run -d chrome --release \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

### Tests et validation

```bash
# Analyser le code
flutter analyze

# Formater le code
flutter format lib/

# Exécuter les tests
flutter test

# Vérifier les dépendances
flutter pub outdated
```

### Build

```bash
# Build web
flutter build web

# Build APK (Android)
flutter build apk

# Build iOS
flutter build ios

# Build Windows
flutter build windows
```

## Supabase

### Configuration

```bash
# Copier le template
cp services/backend/.env.example services/backend/.env

# Éditer avec vos credentials
nano services/backend/.env

# Vérifier la configuration
cat services/backend/.env
```

### Base de données

```bash
# Créer les tables
python3 services/backend/migrate.py

# Vérifier dans Supabase Studio
open https://supabase.com
```

## Développement

### Ajouter une nouvelle page Flutter

```bash
# Créer le fichier
touch apps/mobile/lib/src/features/my_feature/my_page.dart

# Ajouter la route dans app_shell.dart
# Importer et utiliser la page
```

### Ajouter un nouvel endpoint API

```bash
# Ajouter le modèle dans app/models.py
# Ajouter le schéma dans app/schemas.py
# Ajouter la route dans app/main.py
# Tester avec curl ou Swagger
```

### Ajouter un nouveau provider Riverpod

```bash
# Créer le fichier dans lib/src/providers/
# Définir le provider
# Utiliser dans les pages avec ref.watch()
```

## Debugging

### Flutter

```bash
# Logs détaillés
flutter run -v

# Attacher un debugger
flutter attach

# Vérifier les performances
flutter run --profile

# Trace les performances
flutter run --trace-startup
```

### Backend

```bash
# Logs détaillés
uvicorn app.main:app --reload --log-level debug

# Vérifier les erreurs
tail -f sedapps.db.log

# Accéder à la base de données
sqlite3 sedapps.db
```

### Network

```bash
# Vérifier la connexion
curl -v http://localhost:8000/docs

# Voir les headers
curl -i http://localhost:8000/v1/account

# Tester avec un token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/v1/account
```

## Nettoyage

```bash
# Supprimer la base de données
rm services/backend/sedapps.db

# Supprimer les caches Flutter
flutter clean

# Supprimer les dépendances
rm -rf apps/mobile/pubspec.lock
flutter pub get

# Supprimer l'environnement virtuel
rm -rf services/backend/.venv
```

## Déploiement

### Préparation

```bash
# Vérifier que tout compile
flutter analyze
python3 -m py_compile services/backend/app/*.py

# Build production
flutter build web --release
```

### Déployer le backend

```bash
# Sur Heroku
heroku create sedapps-backend
heroku config:set SEDAPPS_SUPABASE_URL=...
heroku config:set SEDAPPS_SUPABASE_KEY=...
git push heroku main

# Sur Vercel/Netlify (avec serverless)
# Voir la documentation respective
```

### Déployer Flutter

```bash
# Sur Firebase Hosting
firebase deploy --only hosting

# Sur Netlify
netlify deploy --prod --dir=build/web

# Sur GitHub Pages
flutter build web
git add build/web
git commit -m "Deploy web"
git push
```

## Ressources

- Flutter Docs : https://flutter.dev/docs
- FastAPI Docs : https://fastapi.tiangolo.com
- Supabase Docs : https://supabase.com/docs
- Riverpod Docs : https://riverpod.dev
- SQLAlchemy Docs : https://sqlalchemy.org
