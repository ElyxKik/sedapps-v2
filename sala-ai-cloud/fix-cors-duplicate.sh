#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"

echo "🔧 Suppression CORS dupliqués dans Nginx"

ssh "$SERVER_USER@$SERVER_IP" << 'NGINX_FIX'
cat > /etc/nginx/sites-available/sedapps << 'EOF'
server {
    listen 80;
    server_name api.winandbet.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name api.winandbet.online;

    ssl_certificate /etc/letsencrypt/live/api.winandbet.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.winandbet.online/privkey.pem;

    location / {
        proxy_pass http://172.18.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF

nginx -t && systemctl reload nginx
echo "✅ Nginx rechargé sans CORS dupliqués"
NGINX_FIX

echo "✅ Terminé — FastAPI gère désormais les CORS seul"
