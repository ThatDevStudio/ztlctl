---
title: Troubleshooting
nav_order: 12
---

# Troubleshooting

## Common Issues

### "ztlctl: command not found"

**Cause**: The CLI is not on your PATH.

**Fix**:
- If installed with `pip install ztlctl`, ensure your Python scripts directory is on PATH
- If installed with `uv tool install ztlctl`, ensure `~/.local/bin` is on PATH
- Verify: `python -m ztlctl --version`

### "No vault found"

**Cause**: ztlctl must be run from a vault root (directory containing `ztlctl.toml`) or a subdirectory.

**Fix**:
```bash
# Initialize a new vault
ztlctl init my-vault
cd my-vault

# Or specify a config path
ztlctl --config /path/to/ztlctl.toml <command>
```

### "Database locked"

**Cause**: Another process has an open connection to the SQLite database.

**Fix**:
- Close other ztlctl processes or MCP server instances
- If the issue persists after closing all processes, the WAL file may be stale:
  ```bash
  # This is safe — SQLite will recover on next connection
  rm .ztlctl/ztlctl.db-wal .ztlctl/ztlctl.db-shm
  ```

### "MCP server not starting"

**Cause**: Missing the `[mcp]` optional extra.

**Fix**:
```bash
pip install ztlctl[mcp]
# or
uv tool install ztlctl --with mcp
```

### "Semantic search not available"

**Cause**: Missing the `[semantic]` optional extra.

**Fix**:
```bash
pip install ztlctl[semantic]
```

Check status: `ztlctl vector status`

### "Reweave finds no connections"

**Possible causes**:
- `min_score_threshold` is too high (default: 0.6)
- Not enough content for meaningful similarity

**Fix**:
```bash
# Lower the threshold
ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD=0.3 ztlctl reweave --auto-link-related

# Or update ztlctl.toml
# [reweave]
# min_score_threshold = 0.4
```

### Vault appears corrupted

**Fix** — rebuild the database from files:
```bash
# Full rebuild from markdown files on disk
ztlctl check --rebuild
```

If that fails, delete the database and rebuild:
```bash
rm .ztlctl/ztlctl.db
ztlctl check --rebuild
```

### Rollback to last backup

```bash
ztlctl check --rollback
```

Backups are retained for 30 days (configurable via `[check] backup_retention_days`).

## Getting Help

- [GitHub Issues](https://github.com/ThatDevStudio/ztlctl/issues) — Bug reports and feature requests
- [GitHub Discussions](https://github.com/ThatDevStudio/ztlctl/discussions) — Questions and community support
