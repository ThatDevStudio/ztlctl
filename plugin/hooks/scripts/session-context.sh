#!/usr/bin/env bash
# SessionStart hook: inject vault context so Claude is immediately oriented.
# Falls back gracefully if ztlctl is not installed or no vault is found.

set -euo pipefail

if ! command -v ztlctl &>/dev/null; then
  echo "ztlctl not found. Install with: pipx install ztlctl"
  exit 0
fi

# Check if we're in a vault (ztlctl.toml exists or ZTLCTL_VAULT is set)
if [ ! -f "ztlctl.toml" ] && [ -z "${ZTLCTL_VAULT:-}" ]; then
  exit 0
fi

echo "=== ztlctl Vault Context ==="

# Recent activity
RECENT=$(ztlctl query list --json --sort recency --limit 5 2>/dev/null || true)
if [ -n "$RECENT" ]; then
  echo "--- Recent Activity (last 5 items) ---"
  echo "$RECENT"
fi

# Work queue
WORK_QUEUE=$(ztlctl query work-queue --json 2>/dev/null || true)
if [ -n "$WORK_QUEUE" ]; then
  echo "--- Work Queue ---"
  echo "$WORK_QUEUE"
fi

echo "=== End Vault Context ==="
