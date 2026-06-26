#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔄 Mise à jour des CORS..."
echo ""

# Mettre à jour le .env avec les CORS Firebase
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/sedapps

# Sauvegarder l'ancien .env
cp .env .env.backup

# Mettre à jour CORS_ORIGINS
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=https://sedapps.web.app,http://localhost:3000,http://localhost:8080,http://193.168.175.108:8000|g' .env

# Vérifier la mise à jour
echo "✅ CORS mis à jour:"
grep CORS_ORIGINS .env

# Redémarrer les services
echo "🔄 Redémarrage des services..."
docker compose restart core-api ai-orchestrator

# Attendre
sleep 10

# Vérifier l'état
docker compose ps
EOF

echo ""
echo "✨ CORS configurés!"
echo ""
echo "🔍 Tester:"
echo "  curl -H 'Origin: https://sedapps.web.app' https://api.winandbet.online/v1/auth/login"
