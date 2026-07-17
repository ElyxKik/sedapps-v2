#!/usr/bin/env bash
# Deploy source code only. Production secrets stay in /opt/sedapps/.env.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
cd "$SCRIPT_DIR"

SERVER_HOST="${SERVER_HOST:-193.168.175.108}"
SERVER_USER="${SERVER_USER:-root}"
REMOTE_PATH="${REMOTE_PATH:-/opt/sedapps}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/sedapps_deploy_ed25519}"
COMPOSE_FILE="docker-compose.prod.yml"
RELEASE_REVISION="$(git -C "$REPO_ROOT" rev-parse HEAD)"

if [[ ! -r "$SSH_KEY" ]]; then
  echo "SSH key not found: $SSH_KEY" >&2
  exit 1
fi

ssh_cmd=(ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
rsync_ssh="ssh -i $SSH_KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

"${ssh_cmd[@]}" "$SERVER_USER@$SERVER_HOST" "install -d -m 750 '$REMOTE_PATH'"

# Never transfer secrets, development dependencies, generated output, or local credentials.
rsync -az --delete \
  --exclude='.git/' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='.venv/' \
  --exclude='node_modules/' \
  --exclude='.dart_tool/' \
  --exclude='.next/' \
  --exclude='build/' \
  --exclude='dist/' \
  --exclude='__pycache__/' \
  --exclude='.deployed-revision' \
  --exclude='*.dump' \
  --exclude='*.backup' \
  --exclude='*.before-*' \
  -e "$rsync_ssh" \
  ./ "$SERVER_USER@$SERVER_HOST:$REMOTE_PATH/"

"${ssh_cmd[@]}" "$SERVER_USER@$SERVER_HOST" "
  set -Eeuo pipefail
  cd '$REMOTE_PATH'
  test -s .env || { echo 'Missing production .env' >&2; exit 1; }
  docker compose -f '$COMPOSE_FILE' config --quiet
  docker compose -f '$COMPOSE_FILE' build --pull --no-cache
  docker compose -f '$COMPOSE_FILE' run --rm core-api alembic upgrade head
  docker compose -f '$COMPOSE_FILE' up -d --force-recreate --remove-orphans
  docker compose -f '$COMPOSE_FILE' ps
  curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
  printf '%s\n' '$RELEASE_REVISION' > .deployed-revision
  docker image prune -f >/dev/null
  docker builder prune -f --filter 'until=24h' >/dev/null
"

echo "Deployment $RELEASE_REVISION completed successfully."
