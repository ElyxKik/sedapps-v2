#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔧 Fix rôle PostgreSQL + migrations"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

echo "=== Vérification .env DB vars ==="
grep -E '^(DATABASE_URL|POSTGRES_)' .env

PG_USER=$(grep '^POSTGRES_USER=' .env | cut -d= -f2)
PG_PASS=$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2)
PG_DB=$(grep '^POSTGRES_DB=' .env | cut -d= -f2)

echo "User: $PG_USER / DB: $PG_DB"

echo "=== Recréer le rôle avec le bon mot de passe ==="
docker compose exec -T postgres psql -U postgres << SQL
DO \$\$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = '$PG_USER') THEN
    ALTER ROLE "$PG_USER" WITH PASSWORD '$PG_PASS';
  ELSE
    CREATE ROLE "$PG_USER" WITH LOGIN PASSWORD '$PG_PASS';
  END IF;
END
\$\$;

DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$PG_DB') THEN
    CREATE DATABASE "$PG_DB" OWNER "$PG_USER";
  END IF;
END
\$\$;

GRANT ALL PRIVILEGES ON DATABASE "$PG_DB" TO "$PG_USER";
SQL

echo "=== Test connexion avec les bons credentials ==="
docker compose exec -T postgres psql -U $PG_USER -d $PG_DB -c '\dt' || echo "Pas encore de tables"

echo "=== Restart core-api ==="
docker compose restart core-api
sleep 8

echo "=== Exécution migrations via core-api ==="
docker compose exec -T core-api python3 -c "
from app.db.base import Base
from app.db.session import engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('Tables créées:', list(Base.metadata.tables.keys()))
" 2>&1

echo "=== Tables après migration ==="
docker compose exec -T postgres psql -U $PG_USER -d $PG_DB -c '\dt'

echo "=== Logs core-api ==="
docker compose logs core-api --tail=20

echo "=== Test register ==="
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d "{
    \"email\":\"kikuniely@gmail.com\",
    \"password\":\"MyxeezyLife*\",
    \"full_name\":\"Kikuni Ely\",
    \"org_name\":\"Sedapps\"
  }" | python3 -m json.tool 2>&1 || true
EOF

echo "\n🧪 Test HTTPS register"
curl -s -X POST https://api.winandbet.online/v1/auth/register \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://sedapps.web.app' \
  -d '{
    "email":"kikuniely@gmail.com",
    "password":"MyxeezyLife*",
    "full_name":"Kikuni Ely",
    "org_name":"Sedapps"
  }' | python3 -m json.tool 2>&1 || true

echo "\n✅ Terminé"
