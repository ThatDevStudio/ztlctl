# Architecture Remediation Design

**Date:** 2026-03-21
**Status:** Proposed

## Goal

Strengthen the core implementation patterns that now carry most of the platform:

- make post-commit automation reliable for normal CLI usage
- collapse duplicate hook and action execution paths into one canonical write path
- reduce registry/controller/command boilerplate so contribution cost stays reasonable
- centralize plugin and profile discovery so runtime behavior is easier to reason about
- remove compatibility residue that no longer earns its maintenance cost

This document is intentionally implementation-facing. It describes how to fix the patterns surfaced by the architecture review, not user-facing product behavior.

## Background

The documentation, design spec, and recent workspace-profile plans are broadly coherent:

- durable authored artifacts are file-first
- services return `ServiceResult`
- plugin failures must not break core flows
- async plugin work should not block foreground interaction
- the action model is supposed to provide a single source of truth for CLI and MCP surfaces

The current codebase delivers most core features, but two migrations are still half-complete:

1. legacy per-event plugin hooks -> stable `pre_action` / `post_action`
2. hand-written command surfaces -> registry-driven generation

The result is a working system with avoidable duplication and a few correctness risks.

## Problems To Fix

### 1. Event delivery is best-effort, not reliable

The current shutdown path favors non-blocking exit over delivery guarantees:

- `AppContext.close()` shuts the vault down with `wait_for_events=False`
- `EventBus.shutdown()` clears or cancels in-flight work without draining pending WAL rows
- `SessionService.close()` drains only the close event for that invocation

This means slow post-create or post-update hooks can remain `pending` after a normal one-shot CLI run. In practice, a local plugin that sleeps briefly reproduces this immediately.

### 2. Stable `post_action` currently has two producers

`post_action` is emitted in two incompatible ways:

- controllers call it directly with raw input kwargs
- the event bus bridges legacy lifecycle events back into `post_action` with committed payloads

This creates several issues:

- duplicate delivery
- inconsistent payload shapes
- built-in plugins depending on the bridge payload rather than the controller payload
- unclear ordering and unclear source of truth

### 3. The action model has too much glue code

The implementation currently spreads one logical action across:

- an `ActionDefinition` in `_register_core.py`
- a controller method with repeated pre/post hook logic
- a service method
- sometimes a hand-written CLI command anyway

The cost of adding or changing actions is high because the abstraction is not fully paying off. The codebase is already compensating with manual patch points in command registration.

### 4. Plugin/profile discovery is repeated in too many places

Fresh `PluginManager` instances are constructed for:

- dynamic CLI plugin command loading
- workspace profile discovery
- init-step collection
- workflow export surface collection
- live vault runtime event handling

This increases startup churn and makes ordering, warnings, and future caching difficult to standardize.

### 5. Migration residue is accumulating

A few examples:

- dead or effectively dead helpers in `BaseController`
- the deprecated `workspace_modes.py` wrapper still exists even though profile helpers now hold the real logic
- compatibility scaffolding still has to bridge old and new plugin concepts

These are individually small, but together they raise the cognitive load for new contributors.

## Non-Goals

- no user-facing command redesign in this phase
- no change to the file-first durability contract
- no change to the plugin capability model
- no rewrite of every large service module in one pass
- no forced public deprecation of working commands unless the internal path is first stabilized

## Design Decisions

### 1. There will be one canonical write-side event source

For mutating operations, the canonical sequence becomes:

1. command surface gathers inputs
2. action executor runs synchronous `pre_action`
3. service performs validation, transaction, and persistence
4. service emits one post-commit action event
5. event bus delivers stable `post_action`
6. legacy lifecycle hooks are supported only as adapters from the stable event, not as first-class producers

This makes the service layer the single producer of post-commit events because it is the only layer that knows:

- whether the write actually committed
- the final content id
- the final path
- the exact changed fields
- any derived metadata needed by plugins

### 2. `pre_action` remains synchronous; `post_action` becomes post-commit only

`pre_action` exists to reject or rewrite inputs before execution. That must remain synchronous.

`post_action` exists to react to successful state changes. For write actions it must run after commit and must not be emitted directly by controllers.

Controller-level direct `post_action` dispatch for write actions should be removed.

For read actions, keep the design simple:

- either do not expose plugin `post_action` hooks for reads yet
- or run them synchronously through one generic executor path

The important rule is that a given action must have exactly one `post_action` producer.

### 3. Introduce a canonical action-event payload

The event bus should carry a stable payload shape, for example:

```python
{
    "action_name": "create_note",
    "side_effect": "write",
    "payload": {
        "id": "ztl_deadbeef",
        "type": "note",
        "title": "Example",
        "path": "notes/example/ztl_deadbeef.md",
        "fields_changed": ["title", "body"],
        "session_id": "LOG-0001",
    },
    "warnings": [...],
}
```

Key points:

- `action_name` is always explicit
- payload shape is action-oriented, not legacy hook-oriented
- plugins no longer need to guess whether kwargs came from controller input or committed output
- the WAL stores one durable representation of a completed write event

### 4. Reverse the compatibility bridge

Today the bridge goes:

- legacy event -> stable `post_action`

That should become:

- stable action event -> optional legacy hook adapters

This direction is much healthier because it establishes the new contract as canonical and lets old hooks degrade toward removal instead of continuing to shape the runtime.

### 5. Make CLI teardown honor event durability

The current non-blocking teardown is only appropriate if another reliable recovery path exists. Since the tool is often invoked one command at a time, the default must favor correctness.

Recommended behavior:

- default CLI shutdown waits for write-side event completion
- if a bounded wait is needed, use a short configurable timeout plus a follow-up WAL drain
- on startup, any pending or failed WAL events from prior runs should be drained before new work begins or at least before shutdown completes

This does not require foreground hook execution during the main action. It only requires the process not to discard its own pending work at exit.

### 6. Replace controller boilerplate with a generic action executor

Most controllers are thin wrappers that repeat:

- build kwargs
- call `_dispatch_pre_action`
- map rejection to `ServiceResult`
- call a service method
- call `_dispatch_post_action`

That should become a reusable executor utility, for example:

```python
executor.run(
    action_name="create_note",
    inputs={...},
    invoke=lambda normalized: CreateService(vault).create_note(...),
)
```

Benefits:

- one implementation of rejection handling
- one implementation of pre-action dispatch
- easier tracing and metrics
- fewer copy-paste controller files

The controller layer can then shrink drastically or disappear behind feature-local action handlers.

### 7. Break up action registration by feature

`_register_core.py` is too large to remain the single registration file.

Preferred direction:

- keep `ActionDefinition` if it still provides value
- move registrations into feature-local modules such as:
  - `actions/create.py`
  - `actions/query.py`
  - `actions/session.py`
  - `actions/workflow.py`
- let the registry compose those modules at import time

This keeps metadata close to the related service/controller code and lowers merge pressure.

### 8. Stop mixing generated and manual command semantics where not needed

The command system should converge toward one of two clear modes per command:

- registry/generated
- intentionally hand-written

The current hybrid patching should be reduced.

Specific actions:

- make `garden seed` a first-class action or an explicit alias over `create_note`
- avoid replacing generated groups in-place where possible
- keep hand-written commands only when their UX truly cannot be described by `ActionDefinition`

### 9. Centralize plugin runtime discovery

Introduce a shared runtime object, conceptually:

```python
PluginRuntime(
    entrypoint_plugins=...,
    local_plugins=...,
    workspace_profiles=...,
    init_steps=...,
    workflow_modules=...,
)
```

Expected properties:

- discovery happens once per process or once per vault context
- warnings are accumulated once
- profile and workflow surfaces read from the same resolved runtime
- vault runtime can register built-ins on top of the same discovered set

This does not require one global singleton. It does require one coherent owner per scope.

### 10. Treat compatibility modules as temporary and time-boxed

After the main remediation lands:

- remove dead controller helpers
- fold `workspace_modes` into `workspace_profiles`
- retire legacy init scaffold wrappers once all built-in and supported plugin flows use the step API directly

Compatibility code should have an exit condition, not just a rationale.

## Proposed Implementation Phases

### Phase 1: Event model hardening

- add a stable post-commit action-event payload model
- emit write-side `post_action` from services only
- remove controller-side write `post_action` dispatch
- change shutdown/startup behavior so pending WAL work is drained reliably
- add regression tests for slow plugin teardown and restart recovery

### Phase 2: Plugin bridge cleanup

- rewrite the legacy bridge so stable action events adapt into legacy hook calls
- keep deprecation warnings for legacy hooks
- update built-in plugins to depend only on the stable payload

### Phase 3: Action execution simplification

- introduce a generic action executor for synchronous pre-action flow
- reduce controller duplication or collapse controllers into smaller action handlers
- migrate `garden seed` onto the canonical action path

### Phase 4: Registry and discovery decomposition

- split `_register_core.py` into feature-local registration modules
- introduce a shared plugin runtime/discovery layer
- route workspace-profile, workflow, and init-step lookups through that shared layer

### Phase 5: Cleanup and residue removal

- remove dead helpers and obsolete wrappers
- tighten docs to describe only the new event/action model
- prune tests that only protect transitional architecture no longer in use

## Validation Plan

### Required regression coverage

- creating a note with a slow local plugin leaves no `pending` WAL rows after normal CLI teardown
- restarting after an interrupted write drains pending action events
- built-in reweave runs exactly once for one create action
- built-in git hooks receive exactly one committed payload shape
- `garden seed` exercises the same pre-action and post-commit machinery as other create flows
- legacy per-event plugins still function through the adapter path during the compatibility window

### Structural assertions

- every write action has exactly one post-commit producer
- no controller emits write-side `post_action` directly
- plugin discovery warnings are consistent across init, workflow, and live vault execution
- registry metadata is colocated with the relevant feature, not concentrated in one monolith

## Risks

### 1. Plugin compatibility breakage

Changing event production order can break plugins that accidentally depend on current duplicate delivery or raw controller kwargs.

Mitigation:

- keep the legacy adapter for one compatibility window
- add fixture-based compatibility tests for representative plugin shapes

### 2. Latency regression at command exit

Waiting for post-commit work can slightly increase command latency.

Mitigation:

- measure current and remediated exit times
- prefer bounded wait plus WAL recovery over fire-and-forget cancellation
- optimize plugin work rather than discarding it

### 3. Large-scope refactor pressure

Action, controller, and plugin runtime cleanup touches many subsystems.

Mitigation:

- land Phase 1 first because it fixes correctness
- keep later phases mechanical and well-scoped
- preserve public command shapes while refactoring internals

## Expected Outcome

After this remediation:

- one-shot CLI usage reliably triggers post-commit automation
- plugins observe one stable payload shape
- action wiring is easier to extend without copy-paste
- profile/workflow/init discovery behaves consistently
- contributors spend less time understanding transitional architecture and more time shipping features

The codebase does not need a rewrite. It needs a clear choice of canonical paths, followed by deliberate removal of the temporary ones.
