---
title: Quick Start
---

# Quick Start

## Research Project Quick Start

Set up a knowledge vault for a focused research project. This workflow covers initialization, source capture, note creation, graph linking, and session tracking.

```bash
# 1. Initialize a new vault
mkdir my-research && cd my-research
ztlctl init --name my-research --topics "python,architecture,devops"
```

The init wizard prompts for vault name, profile, agent tone, and topics when run interactively. Pass `--no-interact` to skip all prompts and use defaults.

```bash
# 2. Start a research session
ztlctl session start "Learning Python async patterns"
```

The session creates a coordination log (`LOG-0001`) and anchors all subsequent work to the topic context. Session close triggers reweave, orphan sweep, and integrity check automatically.

```bash
# 3. Capture a source reference
ztlctl create reference "Python asyncio docs" \
  --url "https://docs.python.org/3/library/asyncio.html" \
  --tags "lang/python,concept/concurrency"
```

References start at `captured` status. Each reference gets a content-hash ID (`ref_XXXXXXXX`) derived from its title.

```bash
# 4. Create synthesis notes as understanding develops
ztlctl create note "Asyncio Event Loop" \
  --tags "lang/python,concept/concurrency" \
  --topic python

ztlctl create note "Async vs Threading Trade-offs" \
  --tags "lang/python,concept/concurrency" \
  --topic python
```

Notes start at `draft` status and progress to `linked` (1+ outgoing links) and `connected` (3+ outgoing links) as reweave adds graph edges. Each note gets a content-hash ID (`ztl_XXXXXXXX`).

```bash
# 5. Track tasks that emerge from research
ztlctl create task "Refactor API to use async" \
  --priority high

# 6. Run reweave to discover connections
ztlctl reweave run
```

Reweave scores note pairs on 4 signals — BM25 lexical similarity, Jaccard tag overlap, graph proximity, and topic match — and adds edges between related content.

```bash
# 7. Search your knowledge
ztlctl query search "async patterns" --rank-by relevance

# 8. Close the session
ztlctl session close --summary "Mapped async patterns, identified refactoring task"
```

Session close runs cross-session reweave, orphan sweep, and an integrity check. No manual cleanup step needed.

---

## Daily Notes Quick Start

Use ztlctl for daily note capture without formal session tracking. This workflow suits knowledge workers who capture continuously and review periodically.

```bash
# 1. Initialize a vault for daily notes
mkdir knowledge-base && cd knowledge-base
ztlctl init --name knowledge-base --profile core --tone minimal --no-interact
```

```bash
# 2. Capture notes as ideas arrive
ztlctl create note "Distributed systems CAP theorem" \
  --tags "systems/distributed,concept/consistency"

ztlctl create note "Event sourcing vs CQRS" \
  --tags "systems/architecture,pattern/cqrs"
```

```bash
# 3. Search and retrieve
ztlctl query search "distributed consistency"

# Filter by type or tag
ztlctl query search "architecture" --type note --tag "systems/architecture"
```

```bash
# 4. Review your work queue
ztlctl query work-queue
```

The work queue scores all actionable items (tasks, stale notes) by priority, impact, and staleness — presented in the order most worth your attention.

```bash
# 5. Connect notes manually or via reweave
ztlctl reweave run --dry-run   # preview suggestions without committing
ztlctl reweave run             # apply suggestions
```

```bash
# 6. Check vault health
ztlctl check --integrity
```

---

## Next Steps

- [Tutorial](tutorial.md) — full step-by-step guide to building a knowledge vault
- [Core Concepts](concepts.md) — content types, lifecycle states, ID patterns, vault structure
- [Knowledge Paradigms](paradigms.md) — capture/synthesis vs enrichment workflows
- [Configuration](configuration.md) — `ztlctl.toml` settings for vault customization
