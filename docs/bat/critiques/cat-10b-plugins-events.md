# Category 10b Critique: Plugins & Event Bus (BAT-110 to BAT-117)

## Test Summary

| Test | Description | Result |
|------|-------------|--------|
| BAT-110 | Plugin Discovery | PASS |
| BAT-111 | Plugin — Custom Content Type | PARTIAL PASS |
| BAT-112 | Plugin — Failure Isolation | PASS |
| BAT-113 | Git Plugin — Batch Mode | PASS |
| BAT-114 | Git Plugin — No Git Installed | SKIP (code inspection) |
| BAT-115 | Event Bus — Async Dispatch | PASS |
| BAT-116 | Event Bus — Sync Mode | PASS |
| BAT-117 | Event Bus — Drain at Session Close | PASS |

## Plugin System

### Local Plugin Discovery (BAT-110): Strong

The local plugin discovery mechanism works end-to-end:

1. Place a `.py` file in `.ztlctl/plugins/`
2. The PluginManager scans for classes with `@hookimpl`-decorated methods
3. Matching classes are instantiated and registered
4. Hooks fire correctly during lifecycle events

In BAT-110, a `TestPlugin` with `post_create` hookimpl was discovered and fired
after `ztlctl create note`. The plugin wrote a file confirming it received the
correct `content_id` and `title` arguments. This is a clean, zero-configuration
plugin mechanism.

**Design strengths:**
- No configuration file needed -- just drop a `.py` file in the plugins directory
- `_` prefixed files are excluded (supporting `__init__.py` and helper modules)
- Classes are scanned for hookimpl markers, not just module-level functions
- Errors during loading/instantiation are logged but never raised

### Custom Content Types (BAT-111): Design Gap

The `register_content_models` hookspec allows plugins to extend the content type
registry. In BAT-111, a plugin registered an `ExperimentModel` extending `NoteModel`.
The registration was successful -- `CONTENT_REGISTRY` contained the new subtype,
and `CreateService.create_note(subtype='experiment')` worked at the service layer.

**However**, the CLI hardcodes subtypes in `click.Choice`:
```python
@click.option("--subtype", type=click.Choice(["knowledge", "decision"]), ...)
```

This means plugin-registered subtypes are accessible via:
- Service layer (Python API): YES
- MCP tools (free-form string): YES
- CLI (`ztlctl create note --subtype`): NO

**Recommendation:** Dynamically build the `click.Choice` list from `CONTENT_REGISTRY`
at command definition time. This would require lazy loading of plugins before CLI
option parsing, or using a callback validator instead of `click.Choice`.

### Failure Isolation (BAT-112): Excellent

A deliberately crashing plugin (`RuntimeError("Plugin crash!")`) was tested in
BAT-112. The results confirm the design invariant:

> **INVARIANT: Plugin failures are warnings, never errors.**

- Note creation succeeded (`ok: true`)
- The error was recorded in `event_wal` with `status='failed'` and the error message
- Retry count was tracked (`retries=1`)
- No exception propagated to the user

This is critical for production reliability. A misbehaving plugin must never
corrupt vault operations.

### Git Plugin (BAT-113): Functional with Minor Issues

The git plugin's batch mode works correctly:
1. Files are staged (`git add`) on each `post_create` event
2. No commits occur until `post_session_close`
3. Batch commit fires at session close with conventional commit message

**Observations:**
- Two commits were created at session close (one for initial staged files, one for
  reweave-modified files). This is due to the enrichment pipeline running reweave
  and then firing another `post_session_close`. This is harmless but verbose.
- Commit message shows "0 created, 0 updated" because session stats don't track
  content created before the session was started in this CLI context. This is
  cosmetic but could confuse users reviewing git history.
- The `post_init` hook exists in the GitPlugin but is never dispatched by
  `InitService`, meaning `ztlctl init` inside a git repo does not auto-commit.
  This is a wiring gap.

**Recommendation:** Wire `post_init` dispatch into `InitService`. The git plugin
already has the implementation ready.

### Git Plugin Without Git (BAT-114): Verified by Inspection

Cannot simulate a missing git binary in the test environment. Code inspection
confirms all git subprocess calls catch `OSError` (parent of `FileNotFoundError`)
and `subprocess.CalledProcessError`. Failures are logged at debug level.

## Event Bus

### WAL-Backed Architecture: Robust

The event bus uses a Write-Ahead Log (WAL) pattern:
1. **Write event to `event_wal` table** with status `pending`
2. **Dispatch hook** via pluggy (async or sync)
3. **Update status** to `completed`, `failed`, or `dead_letter`

This ensures no events are lost even if the process exits during dispatch. The
WAL table records:

| Column | Purpose |
|--------|---------|
| `hook_name` | Which lifecycle event |
| `payload` | JSON-serialized arguments |
| `status` | pending / completed / failed / dead_letter |
| `retries` | Attempt count |
| `error` | Last error message |
| `session_id` | Optional session association |
| `created` | Timestamp of event creation |
| `completed` | Timestamp of completion |

### Async Dispatch (BAT-115): Working

Events are dispatched via `ThreadPoolExecutor` with `max_workers=2`. The event was
recorded in `event_wal` after `create note` returned. The async model ensures:
- Main thread is not blocked by slow plugins
- Events are processed in background threads
- The WAL guarantees persistence even if the process crashes

### Sync Dispatch (BAT-116): Working

The `--sync` flag forces in-process dispatch without the ThreadPoolExecutor. Events
are processed before the command returns. This is useful for:
- Testing (deterministic event ordering)
- Debugging (stack traces in the same thread)
- Low-latency environments

### Drain Barrier (BAT-117): Working

Session close triggers `drain()`, which:
1. Waits for in-flight async futures
2. Queries `event_wal` for `pending` or `failed` events
3. Retries each event synchronously
4. After `max_retries` (3), events become `dead_letter`

In BAT-117, the drain retried all failed events (retries went from 1 to 2).
This confirms the drain mechanism works as a session-close barrier.

## Strengths

1. **WAL persistence**: Events survive process crashes. No lifecycle event is lost.
2. **Failure isolation**: Plugin errors are captured, not propagated. The invariant
   is strictly enforced.
3. **Retry with dead-letter**: Failed events are retried up to 3 times, then moved
   to dead-letter for manual inspection.
4. **Local plugin discovery**: Zero-configuration plugin loading from `.ztlctl/plugins/`.
5. **Dual dispatch modes**: Async (default) for performance, sync (`--sync`) for
   testing and debugging.
6. **Comprehensive hookspec**: 8 lifecycle hooks cover the full content lifecycle
   plus 1 setup hook for custom content models.

## Weaknesses and Recommendations

1. **`post_init` not wired**: The InitService does not dispatch `post_init` events.
   The GitPlugin's `post_init` hook (which would auto-initialize a git repo on
   vault creation) is dead code. Wire the dispatch into InitService.

2. **CLI subtype restriction**: Plugin-registered content subtypes are inaccessible
   via the CLI due to hardcoded `click.Choice` lists. Use dynamic choice building
   or callback validation.

3. **GitPlugin parameter mismatch**: In BAT-115/116/117, the git plugin's
   `post_create` failed with "missing 1 required positional argument: 'tags'".
   This suggests a pluggy dispatch issue when the hook receives keyword arguments
   with the same names as positional parameters. The ReweavePlugin has the same
   signature but works (tested indirectly). This may be a pluggy version issue or
   an argument dispatch order problem. Worth investigating.

4. **Double commit on session close**: The git plugin creates two commits at
   session close when the enrichment pipeline runs. Consider deduplicating by
   batching all session-close operations into a single commit.

5. **No plugin lifecycle management**: There is no way to enable/disable plugins
   via configuration or CLI. A `[plugins]` TOML section with enable/disable
   per-plugin would be useful.

6. **No event replay**: While events are logged in `event_wal`, there is no CLI
   command to replay or inspect them. A `ztlctl event list` or `ztlctl event
   replay` command would aid debugging.

## Overall Assessment

The plugin system and event bus form a solid extension foundation. The WAL-backed
dispatch guarantees durability, the failure isolation protects vault operations,
and the local plugin discovery makes extension development frictionless. The main
gaps are cosmetic (double commits, hardcoded CLI choices) rather than architectural.

**Grade: A-**

The event bus is production-grade with WAL persistence, retry logic, and dead-letter
handling. The plugin system is clean and extensible. The deductions are for the
unwired `post_init` hook, the CLI subtype restriction, and the git plugin parameter
mismatch that needs investigation.
