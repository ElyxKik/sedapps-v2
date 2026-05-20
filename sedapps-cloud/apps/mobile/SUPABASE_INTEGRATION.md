# Intégration Supabase - Flutter

Guide pour connecter l'application Flutter à Supabase via le backend.

## Architecture

```
Flutter App
    ↓
ApiClient (HTTP)
    ↓
Backend FastAPI
    ↓
Supabase PostgreSQL
```

L'application Flutter ne se connecte **pas directement** à Supabase. Elle passe par le backend FastAPI qui gère :
- L'authentification JWT
- Les requêtes à la base de données Supabase
- La logique métier

## Configuration

### 1. Backend configuré avec Supabase

Voir `SUPABASE_SETUP.md` à la racine du projet.

### 2. Variables d'environnement Flutter

Aucune variable Supabase n'est nécessaire dans Flutter. Le backend gère tout.

Lancer Flutter avec :

```bash
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

## Endpoints disponibles

Tous les endpoints du backend sont disponibles :

### Auth
- `POST /v1/auth/register` - Créer un compte
- `POST /v1/auth/login` - Se connecter
- `GET /v1/account` - Récupérer les infos utilisateur

### Projects
- `GET /v1/projects` - Liste des projets
- `POST /v1/projects` - Créer un projet
- `DELETE /v1/projects/{id}` - Supprimer un projet

### CMS
- `GET /v1/projects/{id}/articles` - Articles du projet
- `POST /v1/projects/{id}/articles` - Créer un article
- `PATCH /v1/projects/{id}/articles/{id}` - Modifier un article
- `DELETE /v1/projects/{id}/articles/{id}` - Supprimer un article

## Vérification

1. Lancer le backend avec Supabase configuré
2. Lancer Flutter
3. S'enregistrer et créer un projet
4. Vérifier dans Supabase Studio que les données sont créées

## Troubleshooting

### Les données ne s'affichent pas

1. Vérifier que le backend est connecté à Supabase
2. Vérifier les logs du backend : `docker logs <container_id>`
3. Vérifier dans Supabase Studio que les tables existent

### Erreur d'authentification

1. Vérifier que `CORE_API_BASE_URL` pointe vers le bon backend
2. Vérifier que le token JWT est stocké correctement
3. Vérifier les logs du backend

### Erreur de connexion au backend

1. Vérifier que le backend est lancé
2. Vérifier que le port 8000 est accessible
3. Vérifier les logs du backend
