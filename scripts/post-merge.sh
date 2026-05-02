#!/usr/bin/env bash
# Runs after every task merge. Re-installs JS deps so workspace symlinks and
# any new packages introduced upstream are reconciled before workflows boot.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[post-merge] pnpm install --silent"
pnpm install --silent
