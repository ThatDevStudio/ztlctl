---
title: Quick Start
nav_order: 3
---

# Quick Start

Get a knowledge vault running in 9 commands:

```bash
# 1. Initialize a new vault
ztlctl init my-vault --topics "python,architecture,devops"

# 2. Enter the vault directory
cd my-vault

# 3. Start a research session
ztlctl agent session start "Learning Python async patterns"

# 4. Create notes as you learn
ztlctl create note "Asyncio Event Loop" --tags "lang/python,concept/concurrency"
ztlctl create note "Async vs Threading" --tags "lang/python,concept/concurrency"

# 5. Create references to external sources
ztlctl create reference "Python asyncio docs" --url "https://docs.python.org/3/library/asyncio.html"

# 6. Track tasks that emerge
ztlctl create task "Refactor API to use async" --priority high --impact high

# 7. Let the graph grow — reweave discovers connections
ztlctl reweave --auto-link-related

# 8. Search your knowledge
ztlctl query search "async patterns" --rank-by relevance

# 9. Close the session when done
ztlctl agent session close --summary "Mapped async patterns, identified refactoring task"
```

## Next Steps

- [Tutorial](tutorial.md) — Full step-by-step guide to building a knowledge vault
- [Core Concepts](concepts.md) — Understand content types, lifecycle states, and the knowledge graph
- [Command Reference](commands.md) — All available commands and options
