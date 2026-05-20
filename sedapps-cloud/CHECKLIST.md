# Pre-Launch Checklist

Vérifier que tout est prêt avant de lancer l'application.

## Backend

- [ ] `services/backend/pyproject.toml` - Dépendances installées
- [ ] `services/backend/app/config.py` - Configuration Supabase ajoutée
- [ ] `services/backend/app/database.py` - Support PostgreSQL/Supabase
- [ ] `services/backend/app/models.py` - Modèles SQLAlchemy définis
- [ ] `services/backend/app/main.py` - Routes FastAPI définies
- [ ] `services/backend/migrate.py` - Script de migration créé
- [ ] `services/backend/.env` ou `.env.example` - Variables d'environnement configurées
- [ ] `services/backend/Dockerfile` - Image Docker prête
- [ ] `docker-compose.simple.yml` - Compose configuré

## Flutter

- [ ] `apps/mobile/lib/src/data/api_client.dart` - Client API avec endpoints réels
- [ ] `apps/mobile/lib/src/features/dashboard/dashboard_page.dart` - Stats dynamiques
- [ ] `apps/mobile/lib/src/features/projects/projects_page.dart` - Liste réelle
- [ ] `apps/mobile/lib/src/features/projects/project_detail_page.dart` - Détail avec modals
- [ ] `apps/mobile/lib/src/features/cms/cms_page.dart` - CMS connecté
- [ ] `apps/mobile/lib/src/features/account/account_page.dart` - Compte réel
- [ ] `apps/mobile/lib/src/features/chat/chat_page.dart` - Chat redesigné
- [ ] `flutter analyze` - Pas d'erreurs

## Documentation

- [ ] `QUICKSTART.md` - Guide de démarrage rapide
- [ ] `SUPABASE_SETUP.md` - Configuration Supabase
- [ ] `apps/mobile/SUPABASE_INTEGRATION.md` - Intégration Flutter
- [ ] `services/backend/README.md` - Documentation backend
- [ ] `services/backend/.env.example` - Template variables

## Tests

- [ ] Backend compile : `python3 -m py_compile app/*.py migrate.py`
- [ ] Flutter compile : `flutter analyze`
- [ ] Backend démarre : `uvicorn app.main:app --reload`
- [ ] Flutter démarre : `flutter run -d chrome`
- [ ] Connexion backend ↔ Flutter fonctionne

## Supabase (optionnel)

- [ ] Projet Supabase créé
- [ ] URL et clé copiées
- [ ] `.env` configuré avec credentials
- [ ] `python3 migrate.py` exécuté
- [ ] Tables créées dans Supabase Studio

## Déploiement

- [ ] Backend prêt pour production
- [ ] Flutter prêt pour build
- [ ] Secrets configurés (JWT, Supabase)
- [ ] CORS configuré correctement
- [ ] Logs activés pour debugging

## Notes

- SQLite fonctionne en local sans configuration
- Supabase optionnel pour production
- Tous les endpoints API sont fonctionnels
- Mock data désactivé par défaut
