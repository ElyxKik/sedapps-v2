#!/bin/bash
set -e

# Configuration
SERVER_IP="193.168.175.108"
SERVER_USER="root"
PROJECT_NAME="sala-ai-cloud"
REMOTE_PATH="/opt/sala-ai"
LOCAL_PATH="/Users/elykik/Documents/seda.website/sala-ai-cloud"

echo "🚀 Déploiement de Sala AI sur $SERVER_IP"

# 1. Créer le répertoire distant
echo "📁 Création du répertoire distant..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_PATH"

# 2. Copier le projet
echo "📤 Copie du projet..."
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='.dart_tool' \
  --exclude='build' --exclude='dist' --exclude='__pycache__' \
  --exclude='.env' \
  $LOCAL_PATH/ $SERVER_USER@$SERVER_IP:$REMOTE_PATH/

# 3. Copier le .env (à adapter)
echo "⚙️  Configuration .env..."
ssh $SERVER_USER@$SERVER_IP "cat > $REMOTE_PATH/.env << 'EOF'
# Database
POSTGRES_USER=sedapps
POSTGRES_PASSWORD=sedapps_secure_password_change_me
POSTGRES_DB=sedapps

# Redis
REDIS_URL=redis://redis:6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# API Keys
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENAI_API_KEY=your_openai_key_here

# URLs
CORE_API_URL=http://core-api:8000
AI_ORCHESTRATOR_URL=http://ai-orchestrator:8001
DEPLOY_SERVICE_URL=http://deploy-service:8002

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256

# Locale
DEFAULT_LOCALE=fr
EOF"

# 4. Démarrer Docker Compose
echo "🐳 Démarrage de Docker Compose..."
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose up -d"

# 5. Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 30

# 6. Vérifier l'état
echo "✅ Vérification de l'état..."
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose ps"

# 7. Afficher les URLs
echo ""
echo "✨ Déploiement terminé!"
echo ""
echo "📍 URLs d'accès:"
echo "  - API Core: http://$SERVER_IP:8000"
echo "  - AI Orchestrator: http://$SERVER_IP:8001"
echo "  - Deploy Service: http://$SERVER_IP:8002"
echo "  - Inbox Service: http://$SERVER_IP:8003"
echo "  - Analytics Service: http://$SERVER_IP:8004"
echo "  - Flower (Celery): http://$SERVER_IP:5555"
echo ""
echo "📝 Prochaines étapes:"
echo "  1. Mettre à jour les clés API dans .env sur le serveur"
echo "  2. Configurer Flutter avec: --dart-define=CORE_API_BASE_URL=http://$SERVER_IP:8000"
echo "  3. Vérifier les logs: ssh $SERVER_USER@$SERVER_IP 'cd $REMOTE_PATH && docker compose logs -f'"
