#!/usr/bin/env bash
set -euo pipefail

# ─── Sala AI — Azure Deployment Script ───────────────────
# Usage: ./deploy-azure.sh <server-ip> <ssh-user>

SERVER_IP="${1:?Usage: ./deploy-azure.sh <server-ip> <ssh-user>}"
SSH_USER="${2:?Usage: ./deploy-azure.sh <server-ip> <ssh-user>}"
SSH_TARGET="${SSH_USER}@${SERVER_IP}"

echo "=== Sala AI — Déploiement Azure ==="
echo "Target: ${SSH_TARGET}"
echo ""

# 1. Push latest code
echo "[1/5] Pushing to GitHub..."
git push origin main

# 2. SSH into server and pull
echo "[2/5] Pulling code on server..."
ssh "${SSH_TARGET}" "cd /opt/sala-ai-cloud && git pull origin main"

# 3. Copy env files (if not already present)
echo "[3/5] Checking env files..."
ssh "${SSH_TARGET}" "test -f /opt/sala-ai-cloud/.env || echo 'WARNING: .env missing on server!'"

# 4. Build and start containers
echo "[4/5] Building and starting containers..."
ssh "${SSH_TARGET}" "cd /opt/sala-ai-cloud && docker compose -f docker-compose.prod.yml up -d --build"

# 5. Deploy sedadmin
echo "[5/5] Building and starting admin dashboard..."
ssh "${SSH_TARGET}" "cd /opt/sedadmin && git pull origin main 2>/dev/null || true"
ssh "${SSH_TARGET}" "cd /opt/sedadmin && docker compose -f docker-compose.prod.yml up -d --build"

echo ""
echo "=== Déploiement terminé ==="
echo "Backend:    http://${SERVER_IP}:8000/docs"
echo "Admin:      http://${SERVER_IP}:3001"
echo "Orchestrator: http://${SERVER_IP}:8001/docs"
echo ""
echo "N'oublie pas de configurer Nginx/Caddy pour le HTTPS et les domaines."
