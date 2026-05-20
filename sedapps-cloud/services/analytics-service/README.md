# analytics-service

Service public d'analytics cookieless pour les sites générés.

## Endpoints

- `GET /tracker.js`
- `POST /v1/events`

## Tracker

Inclure dans le site :

```html
<script defer src="https://analytics.example.com/tracker.js" data-tracker-id="sed-project" data-endpoint="https://analytics.example.com"></script>
```

Le tracker capture :

- `pageview`
- clics sur éléments `data-event`
- clic téléphone/email/WhatsApp
- soumissions de formulaires `form[data-track]`

## Privacy

- Respecte `Do Not Track` si `ANALYTICS_RESPECT_DNT=true`.
- Pas de cookies.
- Session stockée en `sessionStorage`.
