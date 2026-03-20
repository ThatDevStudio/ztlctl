# Phase 1: Core Hardening - Research

**Researched:** 2026-03-19
**Domain:** Python CLI hardening — test coverage, performance, schema versioning, type formalization
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Hybrid subtype model**: Subtypes (decision, knowledge, article, tool, spec) CAN have their own lifecycle overrides but inherit from parent by default. DecisionStatus already has its own transition map — formalize that pattern so plugins can do the same.
- **Template references via file paths**: NoteTypeDefinition references templates as file paths (matching current .md.j2 convention). Plugins ship a templates/ directory. No inline template strings.
- Four built-in content types (note, reference, log, task) plus subtypes (decision, knowledge, article, tool, spec) become NoteTypeDefinitions with embedded transition maps.

### Claude's Discretion

- **Lifecycle embedding vs registry**: Whether NoteTypeDefinition embeds its transition map inline or references it via a registry — choose based on downstream Action Registry needs and the 6-layer architecture dependency rules.
- **NoteTypeDefinition layer placement**: Whether it lives in domain/ (pure type, registration in services) or in a new registry package — choose based on dependency direction constraints.
- **Test coverage strategy**: How aggressively to lift pyproject.toml coverage exclusions (session.py, reweave.py, check.py, plugins, MCP). Incremental vs big-bang approach.
- **Schema versioning mechanism**: How to embed version markers in vault databases and detect/upgrade stale vaults via `ztlctl upgrade`.
- **Tech debt / UX / docs audit scope**: Prioritization of the CONCERNS.md items (5 tech debt, 2 bugs, 3 security, 4 performance). Fix all or prioritize by impact.
- **Performance optimization specifics**: ThreadPoolExecutor for rebuild I/O, FTS5 batch scoring approach, betweenness centrality k-approximation parameter.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HARD-01 | Systematic tech debt cleanup — dead code removal, unenforced config enforcement (backup_retention_days, graph auto-materialize), stale index fixes (FTS5/vec divergence after rollback) | Specific files and fix approaches documented in CONCERNS.md; all confirmed in source. FTS5 rollback divergence in check.py line 281; backup_retention_days in check.py/_prune_backups(). |
| HARD-02 | Data model consistency — lifecycle formalization, status transition edge case fixes, garden note protection validation | lifecycle.py has 6 transition maps; content.py has CONTENT_REGISTRY; DecisionModel already demonstrates the subtype-with-custom-lifecycle pattern. |
| HARD-03 | UX polish — CLI rough edges, missing flags, confusing output improvements, progressive disclosure consistency | CONCERNS.md flags Copier recopy fallback not surfaced; check.py rollback warning not prominent. Fragile areas section identifies additional UX gaps. |
| HARD-04 | Documentation audit — incorrect, missing, or unfriendly docs identified and fixed across README, help text, and inline docs | Memory confirms README was updated at v1.1.1; phase should audit current state and fix inconsistencies. |
| HARD-05 | Test coverage gaps closed — session, reweave, check services lifted from coverage exclusion; plugin code (EventBus state machine, GitPlugin modes); MCP _impl functions tested | pyproject.toml omit list confirmed: session.py, reweave.py, check.py, plugins/*. Test files exist (test_session.py, test_reweave.py, test_check.py, test_event_bus.py, test_git_plugin.py) but their coverage is excluded. |
| HARD-06 | Performance bottleneck fixes — rebuild I/O parallelization via ThreadPoolExecutor, FTS5 batch BM25 scoring (single query vs per-candidate), betweenness centrality approximation (k parameter) | check.py line 152-207 (sequential file I/O); reweave.py _score_candidates() (N FTS5 queries); graph.py line 587 (full betweenness_centrality). All confirmed. |
| HARD-07 | Security fixes — Copier trust flag enforcement, MCP HTTP transport binding warning, git commit message newline sanitization | workflow.py uses copier without --trust=false check; serve.py/server.py HTTP bind; git.py lines 72,88 use title directly. All confirmed. |
| HARD-08 | Vault schema versioning with v1→v2 migration path via upgrade command; forward-compatible schema markers | UpgradeService and Alembic infrastructure already exist (services/upgrade.py, infrastructure/database/migrations/). Two migrations in place (001_baseline, 002_node_timestamps). Need v2 migration + stale detection on startup. |
| HARD-09 | NoteTypeDefinition as extensible primitive — formalizes note type + lifecycle transition map + Jinja2 template as one registrable unit; existing 4 content types (note, reference, task, garden) become built-in NoteTypeDefinitions | ContentModel hierarchy, CONTENT_REGISTRY, lifecycle.py transition maps, and build_template_environment() all exist and are the building blocks. |

</phase_requirements>

---

## Summary

Phase 1 is a hardening pass on a mature, well-structured codebase (1256 tests, mypy strict, ruff clean at v1.10.0). The architecture is already excellent — layered Clean Architecture with Vault repository pattern, frozen Pydantic return types, pluggy event bus, Alembic migrations — so this phase adds rigor, not redesign.

The nine requirements cluster into five technical work streams: (1) closing test coverage exclusions on the most complex services (session, reweave, check, plugins, MCP), (2) introducing NoteTypeDefinition as a domain primitive that bundles ContentModel + transition map + template path into one registrable unit, (3) adding a "v2 schema version" marker and stale-schema detection to the already-existing Alembic/UpgradeService infrastructure, (4) fixing six confirmed issues in CONCERNS.md (backup_retention_days enforcement, FTS5/vec rollback divergence, betweenness centrality O(V*E) complexity, rebuild I/O sequential, per-candidate FTS5 queries, Copier trust flag), and (5) auditing and correcting docs/help text.

The dominant implementation risk is NoteTypeDefinition layer placement: the 6-layer architecture places `domain/` as having no internal dependencies beyond pydantic, but `NoteTypeDefinition` needs to reference `ContentModel` (domain) and optionally `build_template_environment()` (infrastructure). The recommendation (see Architecture Patterns) is to keep the frozen dataclass definition in `domain/` and put registration logic in a new `domain/registry.py` that does NOT import infrastructure — template paths stay as strings until resolved by services.

**Primary recommendation:** Work stream by work stream in dependency order — NoteTypeDefinition first (everything else references it), then coverage gaps (requires no new abstractions), then perf + security fixes (isolated), then schema versioning (infrastructure layer), then docs audit (no code risk).

---

## Standard Stack

All tools and libraries are already in-project. No new dependencies required for this phase.

### Core (confirmed from pyproject.toml)

| Library | Version | Purpose | Role in Phase 1 |
|---------|---------|---------|-----------------|
| pytest | >=8.3 | Test runner | Lifting coverage exclusions |
| pytest-cov | >=6.0 | Coverage measurement | Tracking omit list reduction |
| alembic | >=1.13 | Schema migrations | Adding v2 migration, stale detection |
| networkx | >=3.0 | Graph algorithms | betweenness_centrality k-approximation |
| concurrent.futures | stdlib | Thread pool | rebuild I/O parallelization |
| pydantic | >=2.0 | Frozen dataclasses | NoteTypeDefinition model |

### No New Dependencies

This phase is explicitly about hardening, not feature addition. Do not add any new packages. The `concurrent.futures.ThreadPoolExecutor` is stdlib (Python 3.2+). The `k` parameter on `nx.betweenness_centrality()` is a built-in NetworkX approximation option.

**Version verification:** All packages already installed and locked in `uv.lock`. No version changes needed.

---

## Architecture Patterns

### NoteTypeDefinition Design

**Decision: place in `domain/` as a frozen dataclass.**

The 6-layer rule is `domain/ → pydantic only`. `NoteTypeDefinition` itself satisfies this: it holds a `type[ContentModel]` class reference (not an instance), a transition map (a plain dict), and a template path (a str). No infrastructure import needed on the definition.

Registration is a separate concern. Put `NoteTypeRegistry` in `domain/registry.py`. It only imports from `domain/` — no infrastructure, no services. Services resolve template paths using the existing `build_template_environment()` call in `infrastructure/templates.py` — the same way `ContentModel.write_body()` already does.

```python
# src/ztlctl/domain/registry.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ztlctl.domain.content import ContentModel


@dataclass(frozen=True)
class NoteTypeDefinition:
    """Bundled note type: model + lifecycle + template path.

    Instances are the canonical registration unit. Built-in types are
    registered at module load time; plugins call NoteTypeRegistry.register()
    via the register_note_types() hookspec.
    """

    name: str                                   # "note", "decision", "knowledge", ...
    content_type: str                           # parent: "note", "reference", "task"
    model_cls: type[ContentModel]               # Pydantic model for frontmatter
    transitions: dict[str, list[str]]           # status transition map (embedded inline)
    template_name: str                          # Jinja2 body template file name (.md.j2)
    required_sections: list[str] = field(default_factory=list)
    initial_status: str = ""
    is_subtype: bool = False                    # True for decision/knowledge/article/etc.
    parent_type: str | None = None              # For subtypes: which ContentType is parent


class NoteTypeRegistry:
    """Singleton registry of all note types (built-in + plugin-contributed)."""

    def __init__(self) -> None:
        self._types: dict[str, NoteTypeDefinition] = {}

    def register(self, note_type: NoteTypeDefinition) -> None:
        """Register a note type. Validates transition map integrity."""
        self._validate_transitions(note_type)
        self._types[note_type.name] = note_type

    def get(self, name: str) -> NoteTypeDefinition:
        return self._types[name]

    def list_types(self, content_type: str | None = None) -> list[NoteTypeDefinition]:
        if content_type is None:
            return list(self._types.values())
        return [t for t in self._types.values() if t.content_type == content_type]

    def _validate_transitions(self, note_type: NoteTypeDefinition) -> None:
        """Check: all states reachable, no orphaned targets, initial_status valid."""
        ...
```

**Why transitions embedded, not referenced via a separate registry:** Downstream Action Registry (Phase 2) needs to read `NoteTypeDefinition.transitions` to build type-aware CLI/MCP commands. Embedding keeps it self-contained and matches the frozen dataclass pattern. The `DECISION_TRANSITIONS` dict in `lifecycle.py` stays — the built-in `NoteTypeDefinition` for "decision" simply references it: `transitions=DECISION_TRANSITIONS`.

### Built-in Registration Pattern

```python
# src/ztlctl/domain/registry.py  (module-level, after class definitions)
from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS, NOTE_TRANSITIONS,
    REFERENCE_TRANSITIONS, TASK_TRANSITIONS, LOG_TRANSITIONS,
)
from ztlctl.domain.content import (
    NoteModel, KnowledgeModel, DecisionModel,
    ReferenceModel, TaskModel,
)

_REGISTRY = NoteTypeRegistry()

def _register_builtins() -> None:
    _REGISTRY.register(NoteTypeDefinition(
        name="note", content_type="note", model_cls=NoteModel,
        transitions=NOTE_TRANSITIONS, template_name="note.md.j2",
    ))
    _REGISTRY.register(NoteTypeDefinition(
        name="knowledge", content_type="note", model_cls=KnowledgeModel,
        transitions=NOTE_TRANSITIONS, template_name="knowledge.md.j2",
        is_subtype=True, parent_type="note",
    ))
    _REGISTRY.register(NoteTypeDefinition(
        name="decision", content_type="note", model_cls=DecisionModel,
        transitions=DECISION_TRANSITIONS, template_name="decision.md.j2",
        required_sections=["Context", "Choice", "Rationale", "Alternatives", "Consequences"],
        initial_status="proposed", is_subtype=True, parent_type="note",
    ))
    # ... reference, task, log, article, tool, spec ...

_register_builtins()

def get_note_type_registry() -> NoteTypeRegistry:
    return _REGISTRY
```

**Note:** `LogModel` (if it doesn't exist as a class) may need to be added. Currently `lifecycle.py` has `LOG_TRANSITIONS` but `content.py` has no `LogModel` class registered — sessions are stored DB-only. Clarify during planning whether "log" needs a `NoteTypeDefinition` or is excluded.

### Test Coverage Strategy

**Recommended: incremental per-file lift, not big-bang.**

Rationale: session.py (696 lines), reweave.py (819 lines), check.py (905 lines) are large. Adding all tests at once creates a large diff that is hard to review. Lift one file at a time, removing each from the `pyproject.toml` omit list as its tests achieve ≥80% coverage.

The test files already exist (`tests/services/test_session.py`, `tests/services/test_reweave.py`, `tests/services/test_check.py`) — they were written but excluded from coverage. The task is to expand their coverage and remove each file from `omit`.

MCP `_impl` functions: `tests/mcp/` directory exists. The `_impl` functions in `src/ztlctl/mcp/tools.py` were specifically designed to be testable without the `mcp` package. Add unit tests that call `_impl` functions directly. Remove `src/ztlctl/mcp/*` from omit after the most critical `_impl` functions are covered.

Plugin coverage: `tests/plugins/` already has `test_event_bus.py`, `test_git_plugin.py`, `test_reweave_plugin.py`. Expand the EventBus state machine tests (pending→failed→dead_letter paths, timeout edge case). Remove `src/ztlctl/plugins/*` from omit after state machine coverage is added.

**Coverage target order:**
1. `plugins/*` — EventBus state machine + GitPlugin batch mode (clearest paths)
2. `services/check.py` — 4-category scan, backup/restore paths
3. `services/reweave.py` — DISCOVER→SCORE→FILTER→CONNECT stages
4. `services/session.py` — start/close/reopen, enrichment pipeline
5. `mcp/*` — critical `_impl` functions (create, search, session ops)

### Performance Fix Patterns

**rebuild I/O parallelization:**

```python
# src/ztlctl/services/check.py  (inside rebuild())
from concurrent.futures import ThreadPoolExecutor, as_completed

def _read_and_parse(file_path: Path) -> tuple[Path, dict, str]:
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    return file_path, fm, body

files = list(self._vault.find_content())
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(_read_and_parse, f): f for f in files}
    for future in as_completed(futures):
        file_path, fm, body = future.result()
        # ... existing per-file processing ...
```

**FTS5 batch BM25 scoring:**

```python
# src/ztlctl/services/reweave.py  (inside _score_candidates())
# Instead of N individual queries, one ranked FTS5 query:
fts_query = " OR ".join(target_terms)
ranked = conn.execute(
    text(
        "SELECT id, bm25(nodes_fts) AS score "
        "FROM nodes_fts WHERE nodes_fts MATCH :q "
        "ORDER BY bm25(nodes_fts) LIMIT :limit"
    ),
    {"q": fts_query, "limit": len(candidates) * 2},
).fetchall()
bm25_scores = {row.id: abs(row.score) for row in ranked}
```

**betweenness centrality approximation:**

```python
# src/ztlctl/services/graph.py  (inside materialize_metrics())
node_count = g.number_of_nodes()
k = min(node_count, 500) if node_count > 1000 else None  # exact for small graphs
betweenness = nx.betweenness_centrality(g, k=k, seed=42)
```

### Vault Schema Versioning

**The UpgradeService + Alembic infrastructure already exists.** Two migrations are in place (001_baseline, 002_node_timestamps). The "v2" migration needed by HARD-08 is the **third migration** in the chain.

Schema stale detection on startup:

```python
# src/ztlctl/infrastructure/vault.py  (inside Vault._init_db() or lazy init)
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from ztlctl.infrastructure.database.migrations import build_config

def _check_schema_current(self) -> bool:
    cfg = build_config(f"sqlite:///{self._db_path}")
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    with self.engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        current = ctx.get_current_revision()
    return current == head
```

On startup (in AppContext or Vault lazy init), if `_check_schema_current()` returns False, emit a warning:
`"Schema is out of date. Run 'ztlctl upgrade' to apply pending migrations."`

The warning should NOT block operation (users may be running read-only commands). Only `ztlctl check` should treat stale schema as an error category.

### Security Fix Patterns

**Copier trust flag (workflow.py):**

```python
# src/ztlctl/services/workflow.py
import copier

# Add --trust=False enforcement for plugin-contributed templates
copier.run_copy(src=source, dst=str(dest), trust=False)  # not permissive
```

Verify which parameter name Copier 9.x uses. The CONCERNS.md note says "Copier 9.x requires explicit `--trust` flag for hook execution — verify this flag is not being set permissively." Check `copier.run_copy` signature.

**MCP HTTP transport warning (serve.py):**

```python
# src/ztlctl/commands/serve.py
if transport == "http":
    click.echo(
        "WARNING: HTTP transport has no authentication. "
        "Only use on trusted local networks.", err=True
    )
```

**Git commit message sanitization (git.py):**

```python
# src/ztlctl/plugins/builtins/git.py
def _sanitize_for_commit(text: str) -> str:
    """Remove newlines and null bytes from user-supplied text."""
    return text.replace("\n", " ").replace("\r", " ").replace("\0", "")

message = f"ztlctl: create {_sanitize_for_commit(content_id)} — {_sanitize_for_commit(title)}"
```

### Tech Debt Fix Patterns

**backup_retention_days enforcement (check.py `_prune_backups`):**

```python
from datetime import datetime, timedelta

def _prune_backups(self) -> None:
    cfg = self._vault.settings.check
    backups = sorted(self._backup_dir().glob("*.db"), key=lambda p: p.stat().st_mtime)

    # Count-based pruning (existing)
    while len(backups) > cfg.backup_max_count:
        backups.pop(0).unlink()

    # Age-based pruning (new)
    cutoff = datetime.now() - timedelta(days=cfg.backup_retention_days)
    for backup in list(backups):
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff:
            backup.unlink()
            backups.remove(backup)
```

**FTS5/vec divergence after rollback (check.py + check scan):**

The fix has two parts: (1) add a CHECK category that detects divergence after rollback, and (2) document that `check --rollback` should be followed by `check --rebuild`. The divergence itself is architectural (backup is a raw file copy). The pragmatic fix is:
- Add a check category that compares `nodes` count to `nodes_fts` count and flags divergence as a `warning`.
- Add a post-rollback advisory to `check --rollback` output.

**graph auto-materialize (query.py + session close):**

Add `GraphService(self._vault).materialize_metrics()` call at the end of `CheckService.rebuild()`. This ensures that after a rebuild, PageRank is always fresh.

**VEC_CREATE_SQL dead code (schema.py):**

Remove `VEC_CREATE_SQL` from `schema.py` entirely. The `VectorService.ensure_table()` creates the vec table at runtime using the config dimension. The schema.py constant is not used for creation and creates a false reference.

### Anti-Patterns to Avoid

- **Don't create a LogModel class** unless audit shows "log" type needs NoteTypeDefinition for Phase 2 Action Registry. Sessions are DB-only with no markdown file; a NoteTypeDefinition with no template path would be misleading.
- **Don't lift ALL coverage exclusions at once** — big-bang removal causes coverage to drop below 80% while test files are partially written. Always lift one file at a time.
- **Don't change ContentModel's public API** — plugins register against `ContentModel`. Adding `NoteTypeDefinition` must not break existing plugin-registered models.
- **Don't run betweenness without the `k` parameter on vaults > 1000 nodes** — this is the most impactful single-line performance fix.
- **Don't block CLI startup on schema check** — stale schema warning must be non-fatal. Only `ztlctl check` should escalate it to an error.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migrations | Custom schema diffing | Alembic (already in project) | Already has migrations, UpgradeService exists |
| Thread pool for I/O | Custom thread management | `concurrent.futures.ThreadPoolExecutor` (stdlib) | Zero deps, battle-tested, already used in EventBus |
| Graph approximations | Custom sampling algorithm | `nx.betweenness_centrality(k=...)` | Built-in NetworkX approximation, documented |
| Coverage measurement | Custom instrumentation | pytest-cov (already in project) | Already configured in pyproject.toml |
| YAML round-trip | Custom YAML parser | ruamel.yaml (already in project) | Preserves comments, already used in content.py |

---

## Common Pitfalls

### Pitfall 1: NoteTypeDefinition Breaks ContentModel Registration

**What goes wrong:** Adding `NoteTypeDefinition` as a new concept while `CONTENT_REGISTRY` still exists creates two parallel registries. Services may look up types in the wrong registry.

**Why it happens:** The existing `CONTENT_REGISTRY` in `content.py` maps `str → type[ContentModel]`. The new `NoteTypeRegistry` maps `str → NoteTypeDefinition`. If the two are not synchronized, `get_content_model("decision")` succeeds but `get_note_type_registry().get("decision")` fails (or vice versa).

**How to avoid:** Keep `CONTENT_REGISTRY` as-is (backward compat, used by services). `NoteTypeDefinition.model_cls` IS the ContentModel class. The two registries share a source of truth — `NoteTypeDefinition` is the authoritative record; `CONTENT_REGISTRY` is populated from it at init time. Add a helper: `get_content_model(name)` that reads from `NoteTypeRegistry` and returns `defn.model_cls`.

**Warning signs:** Any test that calls `get_content_model("knowledge")` starts failing after registry consolidation.

### Pitfall 2: Coverage Exclusion Removal Drops Below 80%

**What goes wrong:** Removing `session.py` from the omit list before writing sufficient tests causes overall coverage to drop below the `fail_under = 80` threshold, breaking CI.

**Why it happens:** session.py is 696 lines. Even with an existing test_session.py, coverage of all branches requires significant test expansion.

**How to avoid:** Before removing a file from omit: run `uv run pytest --cov=ztlctl.services.session --cov-report=term-missing` to see actual coverage for that file alone. Only remove from omit when that file reaches ≥80%.

**Warning signs:** CI failure with `FAIL Required test coverage of 80% not reached`.

### Pitfall 3: ThreadPoolExecutor in rebuild() Breaks Transaction Atomicity

**What goes wrong:** Parallelizing file reads in `CheckService.rebuild()` is safe, but if any file write (after re-parsing) is also parallelized, SQLite's transaction model will serialize or fail with "database is locked".

**Why it happens:** SQLite in WAL mode allows concurrent reads but serializes writes. Multiple threads writing to the same connection raises `OperationalError`.

**How to avoid:** Parallelize ONLY the file READ phase (I/O-bound). Keep the DB write phase sequential in a single `vault.transaction()` context. The parallel step collects `(file_path, frontmatter, body)` tuples; the sequential step processes them one by one inside the transaction.

**Warning signs:** `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked` during rebuild with parallelization enabled.

### Pitfall 4: Alembic Version Stamp Blocks Pre-Alembic Vault Upgrade

**What goes wrong:** Pre-Alembic vaults (created before migration 001_baseline was introduced) have tables but no `alembic_version` row. The stale-schema detection sees `current=None` (no version stamp) and warns even though the vault is schema-current.

**Why it happens:** `MigrationContext.get_current_revision()` returns `None` for un-stamped databases. Comparing `None != head` is always True.

**How to avoid:** The existing `UpgradeService.apply()` already handles this case: `if current is None and self._tables_exist(): command.stamp(cfg, "head")`. The startup stale check must replicate this logic: `if current is None and tables_exist: not stale`.

**Warning signs:** Every pre-Alembic vault shows "Schema is out of date" on every startup even after running `ztlctl upgrade`.

### Pitfall 5: FTS5 Batch Query With Complex Term Sets

**What goes wrong:** Reformulating per-candidate BM25 queries into a single `FTS5 MATCH` query fails when target note terms contain FTS5 special characters (quotes, parentheses, colons).

**Why it happens:** FTS5 `MATCH` uses a query syntax. Unescaped special characters in title/tag terms cause `sqlite3.OperationalError: fts5: syntax error`.

**How to avoid:** Sanitize terms before constructing the FTS5 query. Wrap each term in double quotes: `'"' + term.replace('"', '""') + '"'`. Use `OR` joins for multi-term queries.

**Warning signs:** `OperationalError: fts5: syntax error near "..."` in reweave on notes with special characters in titles.

### Pitfall 6: Test Fixtures for Excluded Services Are Missing

**What goes wrong:** The existing `conftest.py` fixtures were built for services that are tested. The excluded services (session, reweave, check) may need additional fixtures that don't exist yet — e.g., a vault pre-populated with multiple content types, a vault with an active session, a vault with known link patterns for reweave scoring.

**Why it happens:** Tests were stubbed but not developed fully because the services were excluded from coverage.

**How to avoid:** Before lifting each exclusion, audit the existing test file for fixture gaps. Add fixtures to `tests/conftest.py` (shared) or `tests/services/conftest.py` (service-specific).

**Warning signs:** Many `pytest.skip()` or `pass` in test bodies.

---

## Code Examples

### NoteTypeDefinition Full Built-In Registration

```python
# src/ztlctl/domain/registry.py
# Source: analysis of content.py, lifecycle.py, types.py

from __future__ import annotations

from dataclasses import dataclass, field

from ztlctl.domain.content import (
    ContentModel, DecisionModel, KnowledgeModel,
    NoteModel, ReferenceModel, TaskModel,
)
from ztlctl.domain.lifecycle import (
    DECISION_TRANSITIONS,
    LOG_TRANSITIONS,
    NOTE_TRANSITIONS,
    REFERENCE_TRANSITIONS,
    TASK_TRANSITIONS,
)


@dataclass(frozen=True)
class NoteTypeDefinition:
    name: str
    content_type: str
    model_cls: type[ContentModel]
    transitions: dict[str, list[str]]
    template_name: str
    required_sections: list[str] = field(default_factory=list)
    initial_status: str = ""
    is_subtype: bool = False
    parent_type: str | None = None
```

### Removing a File from Coverage Exclusion (pyproject.toml)

```toml
# Before (pyproject.toml)
[tool.coverage.run]
omit = [
    "src/ztlctl/__main__.py",
    "src/ztlctl/mcp/*",
    "src/ztlctl/services/session.py",   # <- remove this line when coverage added
    "src/ztlctl/services/reweave.py",
    "src/ztlctl/services/check.py",
    "src/ztlctl/plugins/*",
]
```

### ThreadPoolExecutor for Rebuild I/O

```python
# src/ztlctl/services/check.py
# Source: CONCERNS.md performance section + Python docs

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def _read_file(path: Path) -> tuple[Path, str]:
    return path, path.read_text(encoding="utf-8")

# In rebuild():
content_files = list(self._vault.filesystem.find_content())
parsed: list[tuple[Path, dict, str]] = []

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(_read_file, f): f for f in content_files}
    for future in as_completed(futures):
        path, raw = future.result()
        fm, body = parse_frontmatter(raw)
        parsed.append((path, fm, body))

# Sequential write phase:
with self._vault.transaction() as txn:
    for path, fm, body in parsed:
        # ... existing per-file DB operations ...
```

### betweenness_centrality with k-approximation

```python
# src/ztlctl/services/graph.py, materialize_metrics()
# Source: NetworkX docs — betweenness_centrality(G, k=None, ...)

node_count = g.number_of_nodes()
# Use exact for small graphs, k-sample approximation for large
k_param = None if node_count <= 500 else min(500, node_count)
betweenness = nx.betweenness_centrality(g, k=k_param, seed=42)
```

---

## State of the Art

| Old Approach | Current Approach | Relevant to Phase 1 |
|--------------|------------------|---------------------|
| Per-candidate FTS5 BM25 queries (N queries) | Single FTS5 MATCH returning ranked results | HARD-06: batch scoring |
| Full `nx.betweenness_centrality(g)` on every materialize | `nx.betweenness_centrality(g, k=500)` approximation | HARD-06: perf fix |
| Sequential `file.read_text()` in rebuild | `ThreadPoolExecutor` parallel reads | HARD-06: I/O fix |
| ContentModel + separate lifecycle maps + separate templates | `NoteTypeDefinition` bundles all three | HARD-09: formalization |
| Coverage exclusion for session/reweave/check/plugins/mcp | Exclusions lifted; tests added | HARD-05: coverage |
| No schema stale warning | Startup check compares Alembic head vs current | HARD-08: versioning |

**Not deprecated:** The `ContentModel` hierarchy, `CONTENT_REGISTRY`, `lifecycle.py` transition maps — all stay. `NoteTypeDefinition` wraps them, not replaces them.

---

## Open Questions

1. **Does "log" (session log) need a NoteTypeDefinition?**
   - What we know: Sessions are DB-only with no markdown file. The `ContentType.LOG` enum exists. `LOG_TRANSITIONS` exists in lifecycle.py. But no `LogModel` class exists in content.py.
   - What's unclear: Phase 2 Action Registry requires NoteTypeDefinitions for auto-generating CLI/MCP commands. If "log" has no NoteTypeDefinition, there can be no auto-generated `create log` command.
   - Recommendation: Create a minimal `LogModel` class (thin ContentModel subclass) and register a `NoteTypeDefinition` for "log" even if the session workflow uses `SessionService` exclusively. Allows Phase 2 to auto-generate discovery without blocking.

2. **How aggressively should we fix CONCERNS.md fragile areas?**
   - What we know: EventBus timeout is hardcoded 30s; dead_letter accumulation; GraphEngine invalidation not automatic. These are in the "fragile areas" section, not the "fix" section.
   - What's unclear: HARD-01 says "systematic tech debt cleanup" — does it include fragile areas or just the 5 explicit tech debt items?
   - Recommendation: Fix only the 5 explicit tech debt items + 2 bugs from CONCERNS.md for HARD-01. Fragile areas are engineering improvements; include the EventBus timeout config option as a low-risk hardening step, skip the GraphEngine auto-invalidation (high complexity).

3. **What is the "v2 schema" for HARD-08?**
   - What we know: Two Alembic migrations exist. UpgradeService is fully functional. The `ztlctl upgrade` command exists.
   - What's unclear: HARD-08 says "vault schema versioning with v1→v2 migration path." There is no "v2" content schema change defined in REQUIREMENTS.md. Is this about adding a new migration file, or just about stale detection?
   - Recommendation: HARD-08 is primarily about adding startup stale detection (warn if not at Alembic head). The "v2 schema" framing means the existing Alembic chain IS the versioning mechanism — no new migration content is required unless NoteTypeDefinition changes the DB schema (it likely does not, since NoteTypeDefinitions live in code, not the DB).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-cov 6.0+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/services/test_check.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HARD-01 | backup_retention_days prunes by age | unit | `uv run pytest tests/services/test_check.py::test_backup_retention_days -x` | ✅ (expand) |
| HARD-01 | FTS5/vec divergence detected after rollback | unit | `uv run pytest tests/services/test_check.py::test_fts_divergence_detection -x` | ❌ Wave 0 |
| HARD-01 | VEC_CREATE_SQL removed from schema.py | unit | `uv run pytest tests/infrastructure/test_schema.py -x` | ✅ (add assertion) |
| HARD-02 | NoteTypeDefinition registered for all 4 content types | unit | `uv run pytest tests/domain/test_registry.py -x` | ❌ Wave 0 |
| HARD-02 | Subtype inherits parent transitions when none provided | unit | `uv run pytest tests/domain/test_registry.py::test_subtype_inherits -x` | ❌ Wave 0 |
| HARD-03 | Copier recopy fallback requires --force-recopy flag | unit | `uv run pytest tests/services/test_workflow.py::test_recopy_flag -x` | ✅ (expand) |
| HARD-04 | README commands match actual CLI help text | manual | manual-only: diff README against `ztlctl --help` output | — |
| HARD-05 | session.py coverage ≥80% | coverage | `uv run pytest --cov=ztlctl.services.session --cov-fail-under=80` | ✅ (expand) |
| HARD-05 | reweave.py coverage ≥80% | coverage | `uv run pytest --cov=ztlctl.services.reweave --cov-fail-under=80` | ✅ (expand) |
| HARD-05 | check.py coverage ≥80% | coverage | `uv run pytest --cov=ztlctl.services.check --cov-fail-under=80` | ✅ (expand) |
| HARD-05 | plugins/* coverage ≥80% | coverage | `uv run pytest --cov=ztlctl.plugins --cov-fail-under=80` | ✅ (expand) |
| HARD-05 | mcp/* _impl functions tested | unit | `uv run pytest tests/mcp/ -x` | ✅ (expand) |
| HARD-05 | EventBus pending→failed→dead_letter state machine | unit | `uv run pytest tests/plugins/test_event_bus.py::test_dead_letter -x` | ❌ Wave 0 |
| HARD-06 | rebuild completes faster with ThreadPoolExecutor | perf regression | `uv run pytest tests/integration/ -k "performance" -x` | ✅ (expand) |
| HARD-06 | reweave uses single FTS5 query, not N | unit | `uv run pytest tests/services/test_reweave.py::test_batch_scoring -x` | ❌ Wave 0 |
| HARD-06 | betweenness uses k-approximation for large graphs | unit | `uv run pytest tests/services/test_graph.py::test_betweenness_approximation -x` | ❌ Wave 0 |
| HARD-07 | git.py sanitizes newlines in commit message | unit | `uv run pytest tests/plugins/test_git_plugin.py::test_commit_message_sanitize -x` | ❌ Wave 0 |
| HARD-07 | serve HTTP transport shows warning | unit | `uv run pytest tests/commands/test_serve.py::test_http_warning -x` | ❌ Wave 0 |
| HARD-08 | Stale schema triggers warning on startup | integration | `uv run pytest tests/integration/test_upgrade.py::test_stale_schema_warning -x` | ❌ Wave 0 |
| HARD-08 | upgrade command applies pending migrations | unit | `uv run pytest tests/services/test_upgrade.py -x` | ✅ |
| HARD-09 | All 4 content types have NoteTypeDefinitions | unit | `uv run pytest tests/domain/test_registry.py -x` | ❌ Wave 0 |
| HARD-09 | Plugin can register custom NoteTypeDefinition | unit | `uv run pytest tests/domain/test_registry.py::test_plugin_registration -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest -x --tb=short -q` (full suite, fast)
- **Per wave merge:** `uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/`
- **Phase gate:** Full suite green + mypy strict + ruff clean before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/domain/test_registry.py` — covers HARD-02, HARD-09 (NoteTypeDefinition + NoteTypeRegistry)
- [ ] `tests/services/test_check.py` (expand) — covers HARD-01 (FTS5 divergence detection test)
- [ ] `tests/services/test_reweave.py` (expand) — covers HARD-06 (batch scoring test)
- [ ] `tests/services/test_graph.py` (expand) — covers HARD-06 (betweenness approximation test)
- [ ] `tests/plugins/test_event_bus.py` (expand) — covers HARD-05 (dead_letter state machine)
- [ ] `tests/plugins/test_git_plugin.py` (expand) — covers HARD-07 (commit message sanitization)
- [ ] `tests/integration/test_upgrade.py` (expand) — covers HARD-08 (stale schema warning)
- [ ] Existing test files for session.py, reweave.py, check.py, plugins/*, mcp/* need expansion before omit removal

---

## Sources

### Primary (HIGH confidence)

- Codebase: `src/ztlctl/domain/lifecycle.py` — confirmed 6 transition maps
- Codebase: `src/ztlctl/domain/content.py` — confirmed ContentModel hierarchy, CONTENT_REGISTRY, register_content_model()
- Codebase: `src/ztlctl/domain/types.py` — confirmed ContentType, NoteSubtype, RefSubtype enums
- Codebase: `src/ztlctl/services/upgrade.py` — confirmed UpgradeService with Alembic BACKUP→MIGRATE→VALIDATE pipeline
- Codebase: `src/ztlctl/infrastructure/database/migrations/versions/` — confirmed 2 existing migrations
- Codebase: `pyproject.toml` — confirmed coverage omit list, fail_under=80, test framework
- Codebase: `src/ztlctl/services/check.py`, `reweave.py`, `session.py` — confirmed line-level locations of all performance bottlenecks
- Codebase: `src/ztlctl/plugins/event_bus.py` — confirmed ThreadPoolExecutor pattern, sync mode
- `.planning/codebase/CONCERNS.md` — authoritative list of tech debt, bugs, security, performance issues
- `.planning/codebase/ARCHITECTURE.md` — confirmed 6-layer dependency rules
- `.planning/codebase/CONVENTIONS.md` — confirmed frozen Pydantic, StrEnum, lazy local imports patterns
- `.planning/research/ARCHITECTURE.md` — NoteTypeDefinition design recommendation with dataclass pattern
- `.planning/research/PITFALLS.md` — Breaking vaults during lifecycle formalization, test infrastructure collapse

### Secondary (MEDIUM confidence)

- NetworkX docs (training data): `nx.betweenness_centrality(G, k=None)` — k parameter for approximation
- Python docs (training data): `concurrent.futures.ThreadPoolExecutor` for I/O parallelization
- FTS5 docs (training data): `bm25()` ranking function, MATCH syntax, special character escaping

### Tertiary (LOW confidence — verify before implementing)

- Copier 9.x `trust` parameter name — CONCERNS.md says "verify this flag is not being set permissively." Check `copier.run_copy` signature in the installed version before implementing the fix.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all tools already installed and confirmed in pyproject.toml
- Architecture (NoteTypeDefinition): HIGH — pattern matches existing frozen dataclass conventions, layer placement follows established rules
- Performance fixes: HIGH — specific line numbers confirmed in source, standard Python patterns
- Test coverage strategy: HIGH — omit list confirmed, test files confirmed to exist
- Schema versioning: HIGH — UpgradeService + Alembic confirmed to be functional infrastructure
- Security fixes: MEDIUM — Copier trust parameter name needs verification against installed version
- Pitfalls: HIGH — all confirmed by cross-referencing CONCERNS.md with actual source

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable codebase; only risk is upstream package API changes)
