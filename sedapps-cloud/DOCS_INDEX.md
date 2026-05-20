# Documentation Index - SedApps

Index complet de la documentation du projet.

## 🚀 Démarrage rapide

1. **[QUICKSTART.md](QUICKSTART.md)** - Commandes pour démarrer en 5 minutes
   - Option 1 : SQLite local
   - Option 2 : Supabase production
   - Option 3 : Docker Compose

2. **[STATUS.md](STATUS.md)** - État actuel du projet
   - Checklist de complétude
   - Statistiques
   - Prochaines étapes

## 📚 Documentation complète

### Architecture et design

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Vue d'ensemble technique
  - Stack technique
  - Composants (Frontend, Backend, DB)
  - Flux de données
  - Sécurité
  - Performance

- **[CHECKLIST.md](CHECKLIST.md)** - Vérification pré-lancement
  - Backend checklist
  - Flutter checklist
  - Documentation checklist
  - Tests checklist

### Configuration et déploiement

- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Configuration Supabase
  - Créer un projet Supabase
  - Récupérer les credentials
  - Configurer le backend
  - Initialiser les tables
  - Troubleshooting

- **[.env.template](.env.template)** - Variables d'environnement
  - Configuration backend
  - Configuration Flutter
  - Configuration déploiement

### Commandes et outils

- **[COMMANDS.md](COMMANDS.md)** - Référence des commandes
  - Backend (installation, tests, Docker)
  - Flutter (installation, build, tests)
  - Supabase (configuration, DB)
  - Développement (ajouter features)
  - Debugging (logs, network)
  - Déploiement (Heroku, Firebase, Netlify)

### Documentation spécifique

- **[services/backend/README.md](services/backend/README.md)** - Backend FastAPI
  - Stack
  - Installation locale
  - Docker Compose
  - Endpoints principaux
  - Notes

- **[apps/mobile/SUPABASE_INTEGRATION.md](apps/mobile/SUPABASE_INTEGRATION.md)** - Flutter + Supabase
  - Architecture
  - Configuration
  - Endpoints disponibles
  - Vérification
  - Troubleshooting

## 🔍 Trouver rapidement

### Je veux...

**Démarrer le projet**
→ [QUICKSTART.md](QUICKSTART.md)

**Comprendre l'architecture**
→ [ARCHITECTURE.md](ARCHITECTURE.md)

**Configurer Supabase**
→ [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

**Lancer des commandes**
→ [COMMANDS.md](COMMANDS.md)

**Vérifier que tout est prêt**
→ [CHECKLIST.md](CHECKLIST.md)

**Connaître l'état du projet**
→ [STATUS.md](STATUS.md)

**Configurer les variables d'environnement**
→ [.env.template](.env.template)

**Développer le backend**
→ [services/backend/README.md](services/backend/README.md)

**Intégrer Flutter avec Supabase**
→ [apps/mobile/SUPABASE_INTEGRATION.md](apps/mobile/SUPABASE_INTEGRATION.md)

## 📖 Lecture recommandée

### Pour les nouveaux développeurs

1. Lire [STATUS.md](STATUS.md) pour comprendre l'état
2. Lire [ARCHITECTURE.md](ARCHITECTURE.md) pour la vue d'ensemble
3. Suivre [QUICKSTART.md](QUICKSTART.md) pour démarrer
4. Consulter [COMMANDS.md](COMMANDS.md) pour les commandes

### Pour la configuration Supabase

1. Lire [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
2. Copier [.env.template](.env.template) en `.env`
3. Remplir les credentials Supabase
4. Exécuter `python3 migrate.py`

### Pour le déploiement

1. Lire [CHECKLIST.md](CHECKLIST.md)
2. Consulter [COMMANDS.md](COMMANDS.md) pour les commandes de build
3. Suivre les instructions de déploiement pour votre plateforme

## 🎯 Fichiers clés du projet

### Backend
- `services/backend/app/main.py` - Routes FastAPI
- `services/backend/app/models.py` - Modèles SQLAlchemy
- `services/backend/app/config.py` - Configuration
- `services/backend/migrate.py` - Script de migration

### Frontend
- `apps/mobile/lib/src/data/api_client.dart` - Client API
- `apps/mobile/lib/src/features/dashboard/` - Dashboard
- `apps/mobile/lib/src/features/projects/` - Gestion projets
- `apps/mobile/lib/src/features/cms/` - CMS articles

### Configuration
- `docker-compose.simple.yml` - Docker Compose
- `services/backend/.env.example` - Variables backend
- `.env.template` - Variables globales

## 📞 Troubleshooting

**Problème** → **Solution**

Backend ne démarre pas
→ Vérifier [COMMANDS.md](COMMANDS.md) section Backend

Flutter ne se connecte pas
→ Vérifier [QUICKSTART.md](QUICKSTART.md) et [COMMANDS.md](COMMANDS.md)

Erreur Supabase
→ Consulter [SUPABASE_SETUP.md](SUPABASE_SETUP.md) section Troubleshooting

Erreur de compilation
→ Vérifier [CHECKLIST.md](CHECKLIST.md) section Tests

## 🔗 Ressources externes

- [Flutter Documentation](https://flutter.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Supabase Documentation](https://supabase.com/docs)
- [Riverpod Documentation](https://riverpod.dev)
- [SQLAlchemy Documentation](https://sqlalchemy.org)

---

**Dernière mise à jour** : Mai 2026
**Version** : 1.0.0
**Status** : ✅ Production Ready
