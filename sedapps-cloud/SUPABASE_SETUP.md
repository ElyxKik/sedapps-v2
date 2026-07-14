# Configuration Supabase

Guide pour connecter le backend SedApps à Supabase.

## Étape 1 : Créer un projet Supabase

1. Aller sur https://supabase.com
2. Cliquer sur "New Project"
3. Remplir les informations :
   - **Name** : sedapps (ou votre nom)
   - **Database Password** : générer un mot de passe fort
   - **Region** : choisir la région la plus proche
4. Cliquer sur "Create new project"
5. Attendre la création (2-3 minutes)

## Étape 2 : Récupérer les credentials

1. Aller dans **Settings > API**
2. Copier :
   - **Project URL** : `https://your-project.supabase.co`
   - **anon public key** : votre clé publique
3. Garder le **Service Role Secret** pour les opérations backend sensibles

## Étape 3 : Configurer le backend

### Option A : Variables d'environnement locales

Créer un fichier `.env` dans `services/backend/` :

```bash
SEDAPPS_SUPABASE_URL=https://your-project.supabase.co
SEDAPPS_SUPABASE_KEY=your-anon-key
SEDAPPS_JWT_SECRET=your-secret-key
```

### Option B : Docker Compose

Éditer `docker-compose.simple.yml` :

```yaml
environment:
  SEDAPPS_SUPABASE_URL: https://your-project.supabase.co
  SEDAPPS_SUPABASE_KEY: your-anon-key
  SEDAPPS_JWT_SECRET: your-secret-key
```

## Étape 4 : Initialiser les tables

Depuis `services/backend/` :

```bash
# Installer les dépendances
pip install -e .

# Créer les tables
python migrate.py
```

Ou avec Docker :

```bash
docker compose -f docker-compose.simple.yml up --build
# Dans un autre terminal
docker compose -f docker-compose.simple.yml exec backend python migrate.py
```

## Étape 5 : Vérifier la connexion

1. Lancer le backend :
   ```bash
   uvicorn app.main:app --reload
   ```

2. Tester un endpoint :
   ```bash
   curl -X POST http://localhost:8000/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```

3. Vérifier dans Supabase Studio que les données sont créées

## Étape 6 : Configurer Flutter

Mettre à jour le backend URL si nécessaire :

```bash
flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://localhost:8000 \
  --dart-define=MOCK_DATA=false
```

## Troubleshooting

### Erreur de connexion PostgreSQL

- Vérifier que `SEDAPPS_SUPABASE_URL` et `SEDAPPS_SUPABASE_KEY` sont corrects
- Vérifier que le projet Supabase est actif
- Vérifier les logs : `docker logs <container_id>`

### Tables non créées

- Exécuter `python migrate.py` manuellement
- Vérifier les permissions dans Supabase Studio

### Authentification échouée

- Vérifier que la clé JWT est la même partout
- Vérifier les logs du backend pour les erreurs

## Notes

- Les migrations SQLAlchemy créent automatiquement les tables
- Supabase fournit une interface web pour gérer les données
- Vous pouvez utiliser Supabase Studio pour inspecter/modifier les données
- Les backups automatiques sont activés par défaut
