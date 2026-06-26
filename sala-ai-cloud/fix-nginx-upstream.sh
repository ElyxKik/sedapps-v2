#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"
FRONTEND_ORIGIN="https://sedapps.web.app"
DOMAIN="api.winandbet.online"

echo "🔧 Correction upstream Nginx vers core-api Docker"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

docker compose up -d core-api
sleep 5

CORE_API_CONTAINER=$(docker ps --filter "label=com.docker.compose.service=core-api" --format '{{.ID}}' | head -n 1)
if [ -z "$CORE_API_CONTAINER" ]; then
  echo "❌ Aucun container core-api actif"
  docker compose ps
  exit 1
fi

CORE_API_IP=$(docker inspect "$CORE_API_CONTAINER" | python3 -c 'import json,sys; d=json.load(sys.stdin)[0]["NetworkSettings"]["Networks"]; print(next((v.get("IPAddress","") for v in d.values() if v.get("IPAddress")), ""))')
if ! printf '%s' "$CORE_API_IP" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "❌ Impossible de trouver l'IP du container core-api"
  echo "Valeur trouvée: $CORE_API_IP"
  echo "Container trouvé: $CORE_API_CONTAINER"
  docker inspect "$CORE_API_CONTAINER" --format '{{json .NetworkSettings.Networks}}' || true
  docker compose ps
  exit 1
fi

echo "✅ IP core-api: $CORE_API_IP"

echo "Test direct container IP:"
curl -i --max-time 10 "http://$CORE_API_IP:8000/health" || true

cat > /etc/nginx/sites-available/sedapps << NGINX
server {
    listen 80;
    server_name api.winandbet.online;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name api.winandbet.online;

    ssl_certificate /etc/letsencrypt/live/api.winandbet.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.winandbet.online/privkey.pem;

    location / {
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://sedapps.web.app" always;
            add_header Access-Control-Allow-Credentials "true" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization,Content-Type,Accept,Origin,User-Agent,DNT,Cache-Control,X-Requested-With" always;
            add_header Access-Control-Max-Age 86400 always;
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }

        add_header Access-Control-Allow-Origin "https://sedapps.web.app" always;
        add_header Access-Control-Allow-Credentials "true" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization,Content-Type,Accept,Origin,User-Agent,DNT,Cache-Control,X-Requested-With" always;

        proxy_pass http://$CORE_API_IP:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
NGINX

nginx -t
systemctl reload nginx
EOF

echo "\n🧪 Test public health"
curl -i --max-time 15 "https://$DOMAIN/health"

echo "\n🧪 Test public docs"
curl -I --max-time 15 "https://$DOMAIN/docs"

echo "✅ Terminé"
