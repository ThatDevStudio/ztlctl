#!/usr/bin/env bash
# PreToolUse hook: block mcp__ztlctl__* calls when no vault is initialized.
# Exit 0 = allow tool call, Exit 2 = block tool call (stderr shown to Claude).

set -euo pipefail

# Check ztlctl is installed
if ! command -v ztlctl >/dev/null 2>&1; then
  echo "ztlctl is not installed. Install it with: pip install ztlctl (or brew install ztlctl)" >&2
  exit 2
fi

# Walk up from CWD looking for vault config
check_dir="$PWD"
while true; do
  if [ -f "${check_dir}/ztlctl.toml" ]; then
    exit 0
  fi
  parent="$(dirname "${check_dir}")"
  if [ "${parent}" = "${check_dir}" ]; then
    break
  fi
  check_dir="${parent}"
done

echo "No ztlctl vault found in this directory. Run 'ztlctl init' to create one, or navigate to an existing vault directory." >&2
exit 2
