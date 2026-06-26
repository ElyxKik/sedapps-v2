#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"

echo "🔍 Diagnostic 502 auth"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e
cd /opt/sedapps

echo "\n=== Docker services ==="
docker compose ps

echo "\n=== Ports listening ==="
ss -tlnp | grep -E ':443|:8000' || true

echo "\n=== Test core-api direct depuis le serveur ==="
curl -i --max-time 10 http://127.0.0.1:8000/health || true
curl -i --max-time 10 http://127.0.0.1:8000/docs | head -40 || true

echo "\n=== Test auth OPTIONS via core-api direct ==="
curl -i --max-time 10 \
  -H 'Origin: https://sedapps.web.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type' \
  -X OPTIONS http://127.0.0.1:8000/v1/auth/register || true

echo "\n=== Test auth POST via core-api direct ==="
curl -i --max-time 20 \
  -H 'Content-Type: application/json' \
  -d '{"email":"debug-'$(date +%s)'@example.com","password":"MyxeezyLife*","full_name":"Debug User"}' \
  http://127.0.0.1:8000/v1/auth/register || true

echo "\n=== Nginx error log ==="
tail -80 /var/log/nginx/error.log || true

echo "\n=== core-api logs ==="
docker compose logs core-api --tail=120 || true
EOF

echo "✅ Diagnostic terminé"
