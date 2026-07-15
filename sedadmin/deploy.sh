#!/usr/bin/env bash
set -Eeuo pipefail

SERVER_HOST="${SERVER_HOST:-193.168.175.108}"
SERVER_USER="${SERVER_USER:-root}"
REMOTE_PATH="${REMOTE_PATH:-/opt/sedadmin}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/sedapps_deploy_ed25519}"

if [[ ! -r "$SSH_KEY" ]]; then
  echo "SSH key not found: $SSH_KEY" >&2
  exit 1
fi

ssh_cmd=(ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
rsync_ssh="ssh -i $SSH_KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

"${ssh_cmd[@]}" "$SERVER_USER@$SERVER_HOST" "install -d -m 750 '$REMOTE_PATH'"

rsync -az --delete \
  --exclude='.git/' \
  --exclude='.env*' \
  --exclude='node_modules/' \
  --exclude='.next/' \
  -e "$rsync_ssh" \
  ./ "$SERVER_USER@$SERVER_HOST:$REMOTE_PATH/"

"${ssh_cmd[@]}" "$SERVER_USER@$SERVER_HOST" "
  set -Eeuo pipefail
  cd '$REMOTE_PATH'
  test -s .env.production || { echo 'Missing .env.production' >&2; exit 1; }
  docker compose -f docker-compose.prod.yml config --quiet
  docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
  docker compose -f docker-compose.prod.yml ps
"

echo "SedAdmin deployment completed successfully."
