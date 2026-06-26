#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔧 Fix core-api production: désactivation uvicorn --reload"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

cp docker-compose.yml docker-compose.yml.backup-prod-fix

python3 - << 'PY'
from pathlib import Path
p = Path('docker-compose.yml')
s = p.read_text()
s = s.replace('uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload', 'uvicorn app.main:app --host 0.0.0.0 --port 8000')
s = s.replace('uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload', 'uvicorn app.main:app --host 0.0.0.0 --port 8001')
s = s.replace('uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload', 'uvicorn app.main:app --host 0.0.0.0 --port 8002')
s = s.replace('uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload', 'uvicorn app.main:app --host 0.0.0.0 --port 8003')
s = s.replace('uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload', 'uvicorn app.main:app --host 0.0.0.0 --port 8004')
p.write_text(s)
PY

echo "Commandes uvicorn actuelles:"
grep -n "uvicorn app.main" docker-compose.yml

docker compose up -d --force-recreate core-api
sleep 8

echo "\n=== core-api ps ==="
docker compose ps core-api

echo "\n=== test direct health ==="
curl -i --max-time 10 http://127.0.0.1:8000/health || true

echo "\n=== logs core-api ==="
docker compose logs core-api --tail=80
EOF

echo "\n🧪 Test HTTPS public"
curl -i --max-time 15 https://api.winandbet.online/health

echo "✅ Terminé"
