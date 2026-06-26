#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
DOMAIN="api.winandbet.online"

echo "🔧 Correction de la configuration HTTPS"
echo ""

# 1. Arrêter les services conflictuels
echo "🛑 Arrêt des services..."
ssh $SERVER_USER@$SERVER_IP << 'STOP_SERVICES'
systemctl stop nginx || true
systemctl stop apache2 || true
cd /opt/sedapps && docker compose down || true
STOP_SERVICES

# 2. Générer le certificat
echo "🔑 Génération du certificat SSL..."
ssh $SERVER_USER@$SERVER_IP "certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN"

# 3. Créer la configuration Nginx
echo "⚙️  Configuration de Nginx..."
ssh $SERVER_USER@$SERVER_IP << 'NGINX_CONFIG'
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

# Activer le site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/sedapps /etc/nginx/sites-enabled/

# Tester et redémarrer
nginx -t
systemctl restart nginx
systemctl enable nginx
NGINX_CONFIG

# 4. Redémarrer Docker
echo "🐳 Redémarrage de Docker..."
ssh $SERVER_USER@$SERVER_IP "cd /opt/sedapps && docker compose up -d"

# 5. Attendre que les services soient prêts
echo "⏳ Attente du démarrage (30s)..."
sleep 30

# 6. Vérifier
echo "✅ Vérification..."
ssh $SERVER_USER@$SERVER_IP "cd /opt/sedapps && docker compose ps"

echo ""
echo "✨ Configuration HTTPS terminée!"
echo ""
echo "📍 Votre API est maintenant accessible:"
echo "  🔒 HTTPS: https://$DOMAIN"
echo "  ✅ Certificat: Let's Encrypt"
echo ""
echo "🔍 Tester:"
echo "  curl https://$DOMAIN/docs"
