#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"
DOMAIN="api.winandbet.online"
FRONTEND_ORIGIN="https://sedapps.web.app"

echo "🔧 Réparation CORS production"

ssh "$SERVER_USER@$SERVER_IP" << EOF
set -e
cd "$REMOTE_PATH"

cp .env .env.cors-backup-
if grep -q '^CORS_ORIGINS=' .env; then
  sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=$FRONTEND_ORIGIN,http://localhost:3000,http://localhost:8080|" .env
else
  echo "CORS_ORIGINS=$FRONTEND_ORIGIN,http://localhost:3000,http://localhost:8080" >> .env
fi

echo "CORS actuel:"
grep '^CORS_ORIGINS=' .env

cat > /etc/nginx/sites-available/sedapps << 'NGINX'
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

        proxy_pass http://127.0.0.1:8000;
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

docker compose restart core-api
sleep 8
EOF

echo "🧪 Test preflight OPTIONS"
curl -i \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -X OPTIONS "https://$DOMAIN/v1/auth/login"

echo "✅ Terminé"
