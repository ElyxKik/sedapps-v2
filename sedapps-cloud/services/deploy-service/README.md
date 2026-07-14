# deploy-service

Service interne responsable de publier un site généré par SedApps Cloud.

## Pipeline

1. Reçoit un `SitePayload` via `POST /v1/deployments/site`.
2. Copie `apps/web-renderer` dans un workspace temporaire.
3. Écrit le payload dans `content/site.json`.
4. Exécute `npm install && npm run build`.
5. Upload le dossier `out/` vers OVH Object Storage (S3 compatible).
6. Configure le DNS OVH pour `slug.sedapps.cloud` si aucun domaine custom n'est fourni.
7. Notifie `core-api` via callback interne si l'endpoint existe.

## Mode dry-run

Par défaut `DEPLOY_DRY_RUN=true` :

- le build Next.js est exécuté réellement ;
- aucun upload S3 réel ;
- aucune modification DNS OVH réelle.

Pour publier réellement :

```env
DEPLOY_DRY_RUN=false
OVH_APP_KEY=...
OVH_APP_SECRET=...
OVH_CONSUMER_KEY=...
OVH_ZONE_NAME=sedapps.cloud
OVH_S3_ENDPOINT=https://s3.gra.io.cloud.ovh.net
OVH_S3_REGION=gra
OVH_S3_BUCKET=...
OVH_S3_ACCESS_KEY=...
OVH_S3_SECRET_KEY=...
OVH_S3_PUBLIC_BASE_URL=https://...
```

## API interne

```bash
curl -X POST http://localhost:8002/v1/deployments/site \
  -H 'Content-Type: application/json' \
  -H "X-Internal-Token: $INTERNAL_API_TOKEN" \
  -d @payload.json
```

Payload attendu :

```json
{
  "deployment_id": "dep_123",
  "tenant_id": "org_123",
  "project_id": "project_123",
  "site_version_id": "version_123",
  "slug": "atelier-solene",
  "custom_domain": null,
  "payload": {}
}
```

`payload` doit être un `SitePayload` valide consommable par `@sedapps/web-renderer`.
