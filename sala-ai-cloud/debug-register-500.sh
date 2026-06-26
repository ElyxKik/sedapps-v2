#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔍 Diagnostic POST /v1/auth/register 500"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set +e
cd /opt/sedapps

echo "=== Logs core-api (dernières 150 lignes) ==="
docker compose logs core-api --tail=150

echo "\n=== Test direct POST /v1/auth/register ==="
curl -i -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"test-'$(date +%s)'@example.com",
    "password":"MyxeezyLife*",
    "full_name":"Test User"
  }' 2>&1 | head -100

echo "\n=== Vérifier la base de données ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c '\dt' 2>&1 | head -20

echo "\n=== Vérifier les tables user ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c 'SELECT * FROM "user" LIMIT 5;' 2>&1 || echo "Table user n'existe pas ou erreur"

echo "\n=== Vérifier les migrations ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c 'SELECT * FROM alembic_version;' 2>&1 || echo "Pas de migrations"
EOF

echo "✅ Diagnostic terminé"
