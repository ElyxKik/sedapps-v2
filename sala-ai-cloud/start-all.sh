#!/bin/bash
set -e

# Configuration
SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sala-ai"
LOCAL_FLUTTER_PATH="/Users/elykik/Documents/seda.website/sala-ai-cloud/apps/mobile"

echo "🚀 Démarrage complet: Docker (serveur) + Flutter (local)"
echo ""

# 1. Démarrer Docker sur le serveur
echo "🐳 Démarrage de Docker sur le serveur $SERVER_IP..."
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose up -d"

# 2. Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services (30s)..."
sleep 30

# 3. Vérifier l'état des services
echo "📊 État des services sur le serveur:"
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose ps"

echo ""
echo "✅ Services démarrés!"
echo ""

# 4. Vérifier que l'API répond
echo "🔍 Vérification de l'API..."
if curl -s http://$SERVER_IP:8000/docs > /dev/null 2>&1; then
  echo "✅ API Core accessible: http://$SERVER_IP:8000"
else
  echo "⚠️  API Core pas encore prête, attente..."
  sleep 10
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Services disponibles:"
echo "  - API Core: http://$SERVER_IP:8000"
echo "  - AI Orchestrator: http://$SERVER_IP:8001"
echo "  - Deploy Service: http://$SERVER_IP:8002"
echo "  - Inbox Service: http://$SERVER_IP:8003"
echo "  - Analytics Service: http://$SERVER_IP:8004"
echo "  - Flower (Celery): http://$SERVER_IP:5555"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 5. Lancer Flutter
echo "🚀 Lancement de Flutter..."
echo ""
cd "$LOCAL_FLUTTER_PATH"

flutter run -d chrome \
  --dart-define=CORE_API_BASE_URL=http://$SERVER_IP:8000 \
  --dart-define=MOCK_DATA=false

echo ""
echo "✨ Application lancée!"
