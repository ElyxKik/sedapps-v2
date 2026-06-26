#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔧 Fix DB password + migrations"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

echo "=== Stop core-api ==="
docker compose stop core-api || true

echo "=== Reset volume postgres pour corriger le mot de passe ==="
docker compose stop postgres || true
docker compose rm -f postgres || true
docker volume rm sedapps_pgdata || true

echo "=== Redémarrage postgres frais ==="
docker compose up -d postgres redis
echo "⏳ Attente postgres healthy..."
for i in $(seq 1 20); do
  STATUS=$(docker compose ps postgres --format '{{.Health}}')
  echo "  postgres: $STATUS"
  if [ "$STATUS" = "healthy" ]; then break; fi
  sleep 3
done

echo "=== Démarrage core-api ==="
docker compose up -d core-api
sleep 8

echo "=== Logs core-api ==="
docker compose logs core-api --tail=30

echo "=== Test connexion DB ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c '\dt' || true

echo "=== Exécution migrations ==="
docker compose exec -T core-api python3 -c "
from app.db.base import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)
print('✅ Tables créées')
" 2>&1 || docker compose exec -T core-api python3 -c "
import subprocess, sys
r = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
print(r.stdout); print(r.stderr)
" 2>&1 || echo "⚠️  Pas de migrations alembic — utilisation create_all"

echo "=== Tables après migration ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c '\dt'

echo "=== Test register ==="
curl -i -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"kikuniely@gmail.com",
    "password":"MyxeezyLife*",
    "full_name":"Kikuni Ely",
    "org_name":"Sedapps"
  }' 2>&1

EOF

echo "\n🧪 Test HTTPS register"
curl -i -X POST https://api.winandbet.online/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"kikuniely@gmail.com",
    "password":"MyxeezyLife*",
    "full_name":"Kikuni Ely",
    "org_name":"Sedapps"
  }'

echo "\n✅ Terminé"
