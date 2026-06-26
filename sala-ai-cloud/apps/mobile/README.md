# SedApps Mobile

Application Flutter **responsive web-first** pour piloter SedApps Cloud depuis mobile, tablette et PC.

## Objectif

Cette app sert d'interface principale pour :

- onboarding d'un projet ;
- génération IA d'un site ;
- édition de sections et design tokens ;
- gestion CMS/blog ;
- suivi analytics et leads ;
- publication via deploy-service OVH.

## Architecture

```text
lib/
  main.dart
  src/
    app.dart                 # MaterialApp.router + routes GoRouter
    core/
      breakpoints.dart       # mobile/tablet/desktop + max-width desktop
      config.dart            # --dart-define CORE_API_BASE_URL
      theme.dart             # Material 3 theme
    data/
      api_client.dart        # Dio + endpoints core-api
      token_store.dart       # shared_preferences
    layout/
      app_shell.dart         # NavigationBar mobile, NavigationRail desktop
    features/
      auth/login_page.dart
      dashboard/dashboard_page.dart
      onboarding/onboarding_page.dart
      editor/editor_page.dart
      cms/cms_page.dart
      publish/publish_page.dart
    widgets/page_scaffold.dart
```

## Responsive design

L'application n'est pas mobile-only :

- mobile : `NavigationBar` bottom ;
- tablette : `NavigationRail` compact ;
- desktop : `NavigationRail` étendu + contenu centré avec max-width ;
- layouts fluides via `LayoutBuilder` ;
- pages scrollables ;
- `SafeArea` ;
- compatible clavier/souris sur web.

## Lancement

Depuis `apps/mobile` :

```bash
flutter pub get
flutter run -d chrome --dart-define=CORE_API_BASE_URL=http://localhost:8000
```

## API utilisée

- `POST /v1/auth/login`
- `POST /v1/auth/register`
- `GET /v1/projects`
- `POST /v1/projects`
- `POST /v1/projects/{project_id}/onboarding`
- `POST /v1/projects/{project_id}/generate`
- `GET /v1/jobs/{job_id}`
- `POST /v1/projects/{project_id}/deploy`
- `GET /v1/projects/{project_id}/articles`

## Affichage des agents IA

Quand une génération est lancée depuis `Brief IA`, l'app :

- crée le projet ;
- sauvegarde le brief onboarding ;
- lance la génération ;
- stocke le `job_id` courant en état Riverpod ;
- affiche l'interaction des agents dans `Dashboard`, `Éditeur` et l'écran dédié `Agents IA`.

La timeline affiche pour chaque agent :

- nom et statut ;
- modèle utilisé ;
- durée ;
- tokens entrants/sortants ;
- warnings ;
- entrée JSON ;
- sortie JSON.

## Prochaines améliorations

- sélection de projet globale ;
- écrans de détail projet ;
- état Riverpod typé par feature ;
- polling automatique du job courant ;
- preview iframe web sur Flutter Web ;
- polling jobs/deployments ;
- écran leads/inbox ;
- écran analytics détaillé.
