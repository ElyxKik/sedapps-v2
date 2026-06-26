#!/bin/bash
set -e

# Configuration
SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sala-ai"
LOCAL_ENV="/Users/elykik/Documents/seda.website/sala-ai-cloud/.env"
TEMP_ENV="/tmp/sala-ai.env"

echo "🔄 Synchronisation du .env vers le serveur..."

# 1. Copier le .env local vers un fichier temporaire
echo "📋 Copie du .env local..."
cp "$LOCAL_ENV" "$TEMP_ENV"

# 2. Modifier les variables pour le serveur (optionnel - adapter selon tes besoins)
echo "✏️  Modification des variables pour le serveur..."

# Exemple: mettre à jour les URLs pour pointer vers le serveur
sed -i '' "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://193.168.175.108:3000,http://193.168.175.108:8080,http://localhost:3000,http://localhost:8080|g" "$TEMP_ENV"
sed -i '' "s|NEXT_PUBLIC_INBOX_URL=.*|NEXT_PUBLIC_INBOX_URL=http://193.168.175.108:8003|g" "$TEMP_ENV"
sed -i '' "s|NEXT_PUBLIC_ANALYTICS_URL=.*|NEXT_PUBLIC_ANALYTICS_URL=http://193.168.175.108:8004|g" "$TEMP_ENV"
sed -i '' "s|DEPLOY_PUBLIC_BASE_URL=.*|DEPLOY_PUBLIC_BASE_URL=https://sedapps.cloud|g" "$TEMP_ENV"

# 3. Envoyer le fichier au serveur
echo "📤 Envoi du .env au serveur..."
scp "$TEMP_ENV" "$SERVER_USER@$SERVER_IP:$REMOTE_PATH/.env"

# 4. Vérifier que le fichier a été copié
echo "✅ Vérification..."
ssh "$SERVER_USER@$SERVER_IP" "ls -lh $REMOTE_PATH/.env"

# 5. Redémarrer les services pour appliquer les changements
echo "🔄 Redémarrage des services..."
ssh "$SERVER_USER@$SERVER_IP" "cd $REMOTE_PATH && docker compose restart"

# 6. Attendre que les services redémarrent
echo "⏳ Attente du redémarrage (30s)..."
sleep 30

# 7. Vérifier l'état
echo "📊 État des services:"
ssh "$SERVER_USER@$SERVER_IP" "cd $REMOTE_PATH && docker compose ps"

# 8. Nettoyer
rm -f "$TEMP_ENV"

echo ""
echo "✨ Synchronisation terminée!"
echo ""
echo "📍 Vérifier les logs:"
echo "  ssh $SERVER_USER@$SERVER_IP 'cd $REMOTE_PATH && docker compose logs -f'"
echo ""
echo "🌐 Accès à l'API:"
echo "  curl http://$SERVER_IP:8000/docs"
