#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/babyhack8x/dev/Applio"
SYNC_SCRIPT="$REPO_DIR/scripts/sync_openclaw_config.py"
COMMIT_MESSAGE="${1:-Sync OpenClaw config backup}"

python3 "$SYNC_SCRIPT"

git -C "$REPO_DIR" add openclaw_config_backup README.md OPENCLAW_SYNC.md scripts

if git -C "$REPO_DIR" diff --cached --quiet; then
  printf 'No OpenClaw config changes to commit.\n'
  exit 0
fi

git -C "$REPO_DIR" commit -m "$COMMIT_MESSAGE"
git -C "$REPO_DIR" push origin main

printf 'OpenClaw config synced and pushed.\n'
