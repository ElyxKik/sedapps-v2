#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔧 Migration DB + test register"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

echo "=== Test connexion DB avec user sedapps ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c '\dt' 2>&1 || echo "Erreur connexion"

echo "=== Redémarre core-api proprement ==="
docker compose stop core-api || true
docker compose up -d core-api
sleep 10

echo "=== Logs démarrage ==="
docker compose logs core-api --tail=20

echo "=== Créer les tables via core-api ==="
docker compose exec -T core-api python3 << 'PYEOF'
import sys
try:
    from app.db.base import Base
    from app.db.session import engine
    import app.models
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées:", list(Base.metadata.tables.keys()))
except Exception as e:
    print(f"❌ Erreur create_all: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

echo "=== Tables créées ==="
docker compose exec -T postgres psql -U sedapps -d sedapps -c '\dt'

echo "=== Test register ==="
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"kikuniely@gmail.com",
    "password":"MyxeezyLife*",
    "full_name":"Kikuni Ely",
    "org_name":"Sedapps"
  }' | python3 -m json.tool 2>&1 || true
EOF

echo "✅ Terminé"
