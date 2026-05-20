# SedAdmin — Tableau de bord administrateur

Application Next.js indépendante pour administrer la plateforme SedApps.

## Démarrage

```bash
cd sedadmin
cp .env.local .env.local.example  # éditer avec vos valeurs
npm install
npm run dev   # → http://localhost:3001
```

## Variables d'environnement

```env
NEXT_PUBLIC_SUPABASE_URL=         # URL Supabase
NEXT_PUBLIC_SUPABASE_ANON_KEY=    # Clé anonyme Supabase
SUPABASE_SERVICE_ROLE_KEY=        # Clé service Supabase (admin)
ADMIN_SECRET=change-me            # Mot de passe d'accès
NEXT_PUBLIC_MAIN_APP_URL=http://localhost:3000
```

## Pages disponibles

| Route | Description |
|---|---|
| `/` | Vue d'ensemble : stats globales, derniers inscrits/projets |
| `/users` | Gestion des utilisateurs : ban/unban, suppression |
| `/subscriptions` | Suivi des abonnements Stripe |
| `/projects` | Liste de tous les projets, suppression |
| `/domains` | Domaines enregistrés |
| `/llm` | Configuration du provider LLM (provider, modèle, clé API) |
| `/activity` | Journal d'activité |
| `/notifications` | Envoi de notifications aux utilisateurs |
| `/settings` | Paramètres de l'instance admin |

## Sécurité

- Accès protégé par `ADMIN_SECRET` via cookie httpOnly
- Middleware Next.js bloque toutes les routes sauf `/login`
- API Supabase utilise la `SUPABASE_SERVICE_ROLE_KEY` (jamais exposée au client)
- La clé API LLM est masquée dans les réponses GET
