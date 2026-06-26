# inbox-service

Service public de réception des formulaires générés.

## Endpoint

- `POST /v1/forms/{form_id}/submit`

Accepte `application/json` ou `multipart/form-data`.

## Sécurité

- Valide uniquement les champs déclarés dans `forms.schema.fields`.
- Vérifie les champs obligatoires.
- Applique une limite de longueur par champ.
- Marque comme spam si le honeypot `website_url` est rempli.

## Stockage

Les soumissions sont enregistrées dans `form_submissions` avec :

- `tenant_id`
- `project_id`
- `form_id`
- `data`
- `ip`
- `user_agent`
- `status`
