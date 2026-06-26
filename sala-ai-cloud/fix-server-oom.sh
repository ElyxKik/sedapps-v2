#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🧠 Correction OOM serveur: ajout swap + redémarrage minimal"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

echo "=== Mémoire avant ==="
free -h

echo "=== Création swap 2G si absent ==="
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
else
  swapon /swapfile || true
fi

echo "=== Mémoire après swap ==="
free -h

echo "=== Stop services non nécessaires temporairement ==="
docker compose stop ai-worker ai-orchestrator deploy-worker deploy-service analytics-service flower inbox-service || true

echo "=== Démarrage services auth minimum ==="
docker compose up -d postgres redis core-api
sleep 10

echo "=== État containers ==="
docker compose ps

echo "=== Logs core-api ==="
docker compose logs core-api --tail=80

echo "=== Test core-api local ==="
curl -i --max-time 10 http://localhost:8000/health || true

echo "=== Mémoire finale ==="
free -h
EOF

echo "\n🧪 Test HTTPS public"
curl -i --max-time 15 https://api.winandbet.online/health || true

echo "✅ Terminé"
