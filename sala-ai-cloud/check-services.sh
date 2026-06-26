#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔍 Vérification des services..."
echo ""

# 1. Vérifier l'état de Docker
echo "📊 État de Docker Compose:"
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose ps"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 2. Si des services sont down, les redémarrer
echo "🔄 Redémarrage des services..."
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose restart"

echo ""
echo "⏳ Attente du démarrage (15s)..."
sleep 15

# 3. Vérifier à nouveau
echo "📊 État après redémarrage:"
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose ps"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Vérifier les logs
echo "📋 Logs de core-api (dernières 20 lignes):"
ssh $SERVER_USER@$SERVER_IP "cd $REMOTE_PATH && docker compose logs core-api --tail=20"

echo ""
echo "✨ Vérification terminée!"
echo ""
echo "🔍 Tester l'API:"
echo "  curl https://api.winandbet.online/docs"
