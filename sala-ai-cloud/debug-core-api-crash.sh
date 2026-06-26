#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔍 Diagnostic crash core-api"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set +e
cd /opt/sedapps

echo "=== docker compose config core-api ==="
docker compose config core-api

echo "\n=== recreate core-api ==="
docker compose up -d --force-recreate core-api
sleep 5

echo "\n=== docker compose ps -a core-api ==="
docker compose ps -a core-api

echo "\n=== docker ps -a matching core-api ==="
docker ps -a --filter "label=com.docker.compose.service=core-api" --no-trunc

CID=$(docker ps -a --filter "label=com.docker.compose.service=core-api" --format '{{.ID}}' | head -n 1)
echo "\nContainer ID: 
$CID"
if [ -n "$CID" ]; then
  echo "\n=== inspect state ==="
  docker inspect "$CID" --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} Error={{.State.Error}} StartedAt={{.State.StartedAt}} FinishedAt={{.State.FinishedAt}}'
fi

echo "\n=== logs core-api last 200 ==="
docker compose logs core-api --tail=200

echo "\n=== env sanity ==="
grep -E '^(DATABASE_URL|POSTGRES_|JWT_SECRET|CORS_ORIGINS)=' .env | sed 's/=.*/=<set>/'

echo "\n=== test published port ==="
curl -i --max-time 5 http://193.168.175.108:8000/health || true
curl -i --max-time 5 http://localhost:8000/health || true
EOF

echo "✅ Diagnostic terminé"
