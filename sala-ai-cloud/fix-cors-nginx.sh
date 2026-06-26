#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"

echo "🔧 Configuration CORS dans Nginx..."
echo ""

ssh $SERVER_USER@$SERVER_IP << 'NGINX_FIX'
cat > /etc/nginx/sites-available/sedapps << 'EOF'
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name api.winandbet.online;

    ssl_certificate /etc/letsencrypt/live/api.winandbet.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.winandbet.online/privkey.pem;

    # Configuration SSL sécurisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # CORS Headers
    add_header 'Access-Control-Allow-Origin' 'https://sedapps.web.app' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;

    # Gérer les requêtes OPTIONS (preflight)
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' 'https://sedapps.web.app' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Content-Type' 'text/plain; charset=utf-8' always;
        add_header 'Content-Length' '0' always;
        return 204;
    }

    # Proxy vers Docker
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Tester et redémarrer
nginx -t && systemctl restart nginx

echo "✅ Nginx configuré avec CORS"
NGINX_FIX

echo ""
echo "✨ CORS Nginx configurés!"
echo ""
echo "🔍 Tester:"
echo "  curl -H 'Origin: https://sedapps.web.app' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: Content-Type' -X OPTIONS https://api.winandbet.online/v1/auth/register -v"
