#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
DOMAIN="api.winandbet.online"

echo "🔒 Configuration HTTPS avec Let's Encrypt"
echo "📍 Domaine: $DOMAIN"
echo "🖥️  Serveur: $SERVER_IP"
echo ""

# 1. Installer Certbot
echo "📦 Installation de Certbot..."
ssh $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
apt-get update
apt-get install -y certbot python3-certbot-nginx nginx
REMOTE_SCRIPT

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
    server_name _;

    ssl_certificate /etc/letsencrypt/live/sedapps.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sedapps.cloud/privkey.pem;

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
        proxy_pass http://core-api:8000;
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

# 4. Configurer le renouvellement automatique
echo "🔄 Configuration du renouvellement automatique..."
ssh $SERVER_USER@$SERVER_IP "systemctl enable certbot.timer && systemctl start certbot.timer"

# 5. Mettre à jour docker-compose.yml
echo "🐳 Mise à jour de Docker Compose..."
ssh $SERVER_USER@$SERVER_IP << 'DOCKER_UPDATE'
cd /opt/sedapps

# Ajouter les volumes pour les certificats SSL
cat >> docker-compose.yml << 'EOF'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/nginx/sites-available/sedapps:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - core-api
    restart: always
EOF

# Redémarrer les services
docker compose up -d
DOCKER_UPDATE

echo ""
echo "✅ Configuration HTTPS terminée!"
echo ""
echo "📍 Votre API est maintenant accessible:"
echo "  🔒 HTTPS: https://$DOMAIN"
echo "  ✅ Certificat: Let's Encrypt"
echo "  🔄 Renouvellement: Automatique"
echo ""
echo "📱 Mettre à jour l'app Flutter:"
echo "  Édite deploy-firebase.sh et change:"
echo "  --dart-define=CORE_API_BASE_URL=https://$DOMAIN"
echo ""
echo "🔍 Vérifier le certificat:"
echo "  curl -v https://$DOMAIN/docs"
