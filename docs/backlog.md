---
title: Hybrid Workspace Closure Record
nav_order: 11
---

# Hybrid Workspace Closure Record

**Status:** Implemented. This page is now a historical record of the hybrid-workspace gap-closure effort.

This document tracks the gap that existed between the original `research` PoC workspace and the current `ztlctl` product, and records how that gap was closed.

The goal is not to recreate the PoC wholesale. The goal is to preserve what `ztlctl` improved while closing the specific gaps that matter to the intended product vision:

- a strong core CLI and service layer
- an opinionated agentic workflow
- a real hybrid machine-layer plus human-garden model
- a plugin-driven workspace/profile system
- a first-party Obsidian starter kit delivered through plugins rather than hardcoded core behavior

## Purpose

This page preserves the design stance, work breakdown, and implementation history of the hybrid workspace closure effort. It is no longer the forward-looking product roadmap.

The work tracked here is explicitly about:

- preserving the stronger `ztlctl` core
- removing architectural drift around hardcoded Obsidian handling
- restoring the intended hybrid machine-layer plus garden-layer model
- doing that through a stronger plugin/profile system
- treating migration parity as secondary

## Design Stance

### Keep as purposeful

- `ztlctl` core as the canonical engine: services, CLI, DB/index, graph, MCP, workflow exports
- file-first durability and rebuildable operational state
- agent workflow portability via MCP and exported client assets
- migration parity with the old repo as a low-priority concern

### Treat as gaps

- hardcoded Obsidian behavior in core
- weak workspace/profile plugin boundary
- reduced hybrid garden model
- shallow Obsidian integration
- spec, docs, and generated self-doc drift

## Impact and Effort Legend

### Impact

- `Critical`: blocks the intended product architecture or undermines trust in the tool
- `High`: materially weakens the hybrid workflow or first-party user experience
- `Medium`: useful and important, but not blocking the target architecture
- `Low`: nice to have or adoption-only

### Effort

- `XS`: less than 1 day
- `S`: 1 to 3 days
- `M`: 3 to 6 days
- `L`: 1 to 2 weeks
- `XL`: 2 to 4 weeks

## Backlog Summary

| ID | Phase | Item | Impact | Effort | Dependencies |
|---|---|---|---|---|---|
| ARC-001 | 0 | Audit hardcoded workspace assumptions | Critical | S | - |
| ARC-002 | 1 | Define workspace profile contract | Critical | M | ARC-001 |
| ARC-003 | 1 | Split `profile` from `viewer` and define deprecation path | High | S | ARC-002 |
| PLG-001 | 2 | Add workspace profile plugin contributions and discovery | Critical | L | ARC-002 |
| PLG-002 | 2 | Route init/workflow through discovered profiles | Critical | M | PLG-001, ARC-003 |
| PLG-003 | 2 | Remove hardcoded Obsidian scaffolding from core | Critical | M | PLG-001, PLG-002 |
| DRF-001 | 0 | Fix generated self-doc terminology and semantics | High | XS | - |
| DRF-002 | 0 | Audit and reconcile spec/docs/implementation drift | High | S | ARC-001 |
| DRF-003 | 2 | Add drift guard tests and checks | High | M | DRF-001, DRF-002 |
| OBS-001 | 3 | Define official Obsidian starter-kit scope | High | M | ARC-002, PLG-001 |
| OBS-002 | 3 | Ship official Obsidian profile plugin scaffolding | Critical | XL | OBS-001, PLG-002 |
| OBS-003 | 4 | Reframe Obsidian ownership after starter scaffold | Medium | S | OBS-002 |
| GDN-001 | 3 | Reintroduce explicit garden scaffold and templates | High | M | OBS-001 |
| GDN-002 | 1 | Codify machine-layer vs garden-layer ownership | Critical | S | ARC-002 |
| GDN-003 | 4 | Align review/export surfaces with hybrid workflow | Medium | M | GDN-001, GDN-002, OBS-002 |
| ADP-001 | 5 | Publish mapping guide from `research` to `ztlctl` | Medium | S | OBS-002, GDN-001 |
| ADP-002 | 5 | Evaluate migration/import tooling | Low | S | ADP-001 |

## Detailed Items

### ARC-001 — Audit hardcoded workspace assumptions

**Problem**
Obsidian and viewer-specific behavior currently appears in core config, init flow, workflow scaffolding, and export behavior without a coherent plugin boundary.

**Outcome**
Produce a complete inventory of every place core assumes a fixed viewer or workspace type.

**Impact**
Critical

**Effort**
S

**Dependencies**
None

**In scope**

- inventory hardcoded `obsidian` and `viewer` branches in `init`, `workflow`, `export`, config defaults, templates, and docs
- identify which assumptions are generic core concerns versus plugin-owned concerns
- identify stale config sections such as `plugins.obsidian` that do not correspond to a real implementation

**Out of scope**

- changing code
- designing the final plugin API

**Acceptance criteria**

- a written inventory exists with file paths and classification for every hardcoded workspace/viewer assumption
- each assumption is tagged as `keep in core`, `move to profile/plugin`, or `remove`
- inventory is sufficient to drive ARC-002 without further repo archaeology

---

### ARC-002 — Define workspace profile contract

**Problem**
The repo lacks a clean concept for plugin-contributed workspace types. Today `viewer` is overloaded and partially stands in for workspace shape.

**Outcome**
Define the public architecture for workspace profiles.

**Impact**
Critical

**Effort**
M

**Dependencies**
ARC-001

**In scope**

- define what a “workspace profile” is
- define what remains core versus what becomes profile-owned
- define first-party expectations for an official profile
- define whether profile-owned assets cover `.obsidian`, garden scaffolding, templates, validation, and upgrade behavior

**Chosen default**

- core keeps generic garden primitives and workflow primitives
- profiles own concrete workspace UX, scaffolding, and viewer-specific assets

**Out of scope**

- implementing plugin hooks
- shipping the Obsidian starter kit

**Acceptance criteria**

- a design note exists that defines profile responsibilities, lifecycle, and boundaries
- the design explicitly states that `vault.client` is no longer the long-term workspace-type abstraction
- the design explicitly states that Obsidian support should be delivered through the plugin ecosystem

---

### ARC-003 — Split `profile` from `viewer` and define deprecation path

**Problem**
`viewer` currently mixes at least two concerns: workspace type and export rendering style.

**Outcome**
Establish two separate concepts:

- `profile`: workspace/setup identity
- `viewer`: optional render target for exports where needed

**Impact**
High

**Effort**
S

**Dependencies**
ARC-002

**In scope**

- decide command and config naming
- define deprecation path for current `client` and `viewer` usage
- decide which existing commands keep `viewer` as a rendering concern versus adopting `profile`

**Chosen default**

- `init` and `workflow` move to `profile`
- `export dashboard --viewer` remains temporarily as a rendering concept until profile-owned export hooks are evaluated

**Acceptance criteria**

- explicit migration rules exist for CLI flags and config
- no implementer needs to guess whether a surface should use `profile` or `viewer`

---

### PLG-001 — Add workspace profile plugin contributions and discovery

**Problem**
The plugin system supports commands, MCP surfaces, workflow modules, and source providers, but not workspace profiles.

**Outcome**
Introduce a first-class profile contribution mechanism.

**Impact**
Critical

**Effort**
L

**Dependencies**
ARC-002

**In scope**

- add a new plugin contract such as `WorkspaceProfileContribution`
- add a new registration hook such as `register_workspace_profiles()`
- extend plugin discovery and validation
- define reserved names and conflict behavior
- make plugin failures non-fatal, consistent with existing plugin behavior

**Out of scope**

- shipping the Obsidian starter kit itself

**Acceptance criteria**

- profiles can be discovered from plugins the same way other contributions are
- duplicate profile ids are rejected safely
- broken profile plugins degrade gracefully without blocking core operations

---

### PLG-002 — Route init/workflow through discovered profiles

**Problem**
Core init and workflow flows currently rely on fixed built-in choices.

**Outcome**
`ztlctl init` and `ztlctl workflow ...` use discovered profiles as the source of available workspace types.

**Impact**
Critical

**Effort**
M

**Dependencies**
PLG-001, ARC-003

**In scope**

- update init and workflow selection logic
- support a default minimal profile when no external profiles are installed
- surface available profiles in help, prompts, and validation
- ensure exported workflow assets can consult the selected profile

**Acceptance criteria**

- profile selection is dynamic
- hardcoded profile/viewer lists are removed from init/workflow setup paths
- a vault can still be initialized without any optional profile plugin installed

---

### PLG-003 — Remove hardcoded Obsidian scaffolding from core

**Problem**
`InitService` currently writes `.obsidian/snippets/ztlctl.css` directly, which contradicts the desired plugin boundary.

**Outcome**
Core stops owning Obsidian-specific file creation.

**Impact**
Critical

**Effort**
M

**Dependencies**
PLG-001, PLG-002

**In scope**

- remove direct Obsidian file writes from core init
- remove stale config assumptions that imply a built-in Obsidian plugin where none exists
- re-home any retained Obsidian behavior behind the official first-party profile/plugin

**Acceptance criteria**

- core init does not mutate `.obsidian/*`
- any Obsidian-specific scaffolding is profile-owned
- config semantics match actual implementation

---

### DRF-001 — Fix generated self-doc terminology and semantics

**Problem**
Generated `self/identity.md` and `self/methodology.md` still describe outdated IDs and lifecycle names.

**Outcome**
Generated self-docs match the real product.

**Impact**
High

**Effort**
XS

**Dependencies**
None

**In scope**

- correct ID patterns
- correct maturity and lifecycle terminology
- correct command references
- remove stale sequential-ID language where implementation uses hashed IDs

**Acceptance criteria**

- generated self-docs match current implementation
- agent-facing self-docs no longer encode known-false rules

---

### DRF-002 — Audit and reconcile spec/docs/implementation drift

**Problem**
The current repo contains meaningful drift across `DESIGN.md`, docs, generated templates, config defaults, and implementation.

**Outcome**
Produce a single reconciled truth set.

**Impact**
High

**Effort**
S

**Dependencies**
ARC-001

**In scope**

- reconcile the expected built-in Obsidian plugin versus actual implementation
- reconcile garden terminology
- reconcile config semantics
- reconcile workflow/export descriptions with actual behavior

**Acceptance criteria**

- every material mismatch is either fixed or explicitly documented as future work
- no major architectural promise remains silently unimplemented in product docs

---

### DRF-003 — Add drift guard tests and checks

**Problem**
Even after cleanup, drift will recur unless enforced.

**Outcome**
Add tests and lightweight guardrails to keep templates, docs, and implementation aligned.

**Impact**
High

**Effort**
M

**Dependencies**
DRF-001, DRF-002

**In scope**

- tests for generated self-doc content
- tests for config defaults and deprecations
- tests for profile discovery and fallback behavior
- optionally snapshot-style checks for key generated assets

**Acceptance criteria**

- obvious terminology and semantic drift becomes test-detectable
- future changes to IDs, lifecycle names, or profile behavior require intentional updates

---

### OBS-001 — Define official Obsidian starter-kit scope

**Problem**
The intended Obsidian role is now “starter kit through plugins,” but the concrete scope is still undefined.

**Outcome**
Define the first-party Obsidian starter kit as a product surface.

**Impact**
High

**Effort**
M

**Dependencies**
ARC-002, PLG-001

**Chosen default**

- first version is a starter kit, not a deep live Obsidian plugin
- shipped as an official first-party profile/plugin using the same public contract as any future third-party profile

**In scope**

- `.obsidian` configuration set
- CSS snippets
- graph color groups
- templates
- community plugin defaults
- workspace/garden directory conventions
- file ownership rules

**Out of scope**

- live bidirectional plugin transport
- embedded UI panels inside Obsidian
- real-time sync workflows

**Acceptance criteria**

- the exact starter-kit artifact set is documented
- ownership of each artifact is defined as `core`, `profile`, or `user-owned`

---

### OBS-002 — Ship official Obsidian profile plugin scaffolding

**Problem**
The repo has no real first-party Obsidian profile despite that being a central intended experience.

**Outcome**
Ship an official first-party profile/plugin that scaffolds the Obsidian starter kit.

**Impact**
Critical

**Effort**
XL

**Dependencies**
OBS-001, PLG-002

**In scope**

- scaffold `.obsidian` defaults
- scaffold starter templates
- scaffold garden directory structure
- scaffold snippet activation and graph group defaults
- provide first-party docs for operating the hybrid vault in Obsidian

**Out of scope**

- indexing garden content into core by default
- live runtime integration with Obsidian plugin APIs

**Acceptance criteria**

- selecting the Obsidian profile creates a coherent hybrid workspace
- starter-kit assets are generated through the profile system, not hardcoded core logic
- the generated vault feels materially closer to the old `research` hybrid experience without regressing core architecture

---

### OBS-003 — Reframe Obsidian ownership after starter scaffold

**Status**
Supersedes the older lifecycle-heavy Phase 4 direction. The current product stance is that the Obsidian starter kit is scaffolded during init and then customized by the user in Obsidian, rather than managed through ztlctl validation and upgrade flows.

**Problem**
The repo still contains wording that implies `.obsidian/` is a long-term profile-managed lifecycle surface, even though the intended direction is a one-shot starter scaffold.

**Outcome**
Docs, templates, and runtime messaging describe `.obsidian/` as a profile-scaffolded workspace surface that ztlctl creates during init and then leaves alone.

**Impact**
Medium

**Effort**
S

**Dependencies**
OBS-002

**In scope**

- remove misleading lifecycle/update language for `.obsidian/`
- clarify that users customize `.obsidian/` after init
- keep API field names such as `managed_paths` for compatibility while narrowing their documented meaning
- document that `garden/` remains human-managed and core indexing still stops at `notes/` and `ops/`

**Acceptance criteria**

- the backlog no longer treats profile validation/update as the default next step
- public docs no longer imply that ztlctl will compare, validate, or rewrite `.obsidian/` after init
- starter-kit messaging clearly states that `.obsidian/` is scaffolded once and then user-managed

---

### GDN-001 — Reintroduce explicit garden scaffold and templates

**Problem**
The hybrid garden model exists in product intent but not as a first-class shipped experience.

**Outcome**
Restore explicit human-owned garden structure through profile scaffolding.

**Impact**
High

**Effort**
M

**Dependencies**
OBS-001

**In scope**

- `garden/notes`
- `garden/groves`
- `garden/library`
- `garden/canvases`
- starter templates for garden note types

**Chosen default**

- garden remains outside core indexing and write paths unless future explicit adapters are added

**Acceptance criteria**

- hybrid vault scaffolding includes a coherent human garden layer
- the garden layer is documented as human-owned
- the scaffold supports the seedling/grove/library patterns that mattered in the old workspace

---

### GDN-002 — Codify machine-layer vs garden-layer ownership

**Problem**
The ownership boundary is part of the intended model, but it is not codified strongly enough in the current product surface.

**Outcome**
Make the boundary explicit in architecture, docs, and tests.

**Impact**
Critical

**Effort**
S

**Dependencies**
ARC-002

**In scope**

- define which paths are machine-owned versus human-owned
- define read/write expectations for agents
- define whether and how links cross the boundary
- preserve current default that core indexing is limited to `notes/` and `ops/`

**Acceptance criteria**

- the boundary is documented as a product invariant
- no implementer needs to infer whether `garden/` should be indexed or mutated by core

---

### GDN-003 — Align review/export surfaces with hybrid workflow

**Status**
Completed through export-purpose clarification and review-surface wording cleanup. The artifact model remains intentionally external and unchanged.

**Problem**
The current review and dashboard surfaces speak about garden work, but they do so from a thinner model than the intended hybrid experience.

**Outcome**
Make review/export outputs coherent with the restored hybrid architecture.

**Impact**
Medium

**Effort**
M

**Dependencies**
GDN-001, GDN-002, OBS-002

**In scope**

- review whether current dashboard export remains generic core behavior or needs profile-aware enrichments
- ensure garden backlog semantics still make sense after explicit garden restoration
- keep export surfaces from becoming accidental replacements for profile-owned workspace UX

**Acceptance criteria**

- review/export outputs are consistent with the hybrid model
- core exports remain useful without over-owning viewer/profile behavior

---

### ADP-001 — Publish mapping guide from `research` to `ztlctl`

**Status**
Completed through `docs/research-mapping.md`.

**Problem**
Even if migration is low priority, there is still value in documenting how the old concepts map to the new product.

**Outcome**
Provide a conceptual mapping guide, not a migration script.

**Impact**
Medium

**Effort**
S

**Dependencies**
OBS-002, GDN-001

**In scope**

- map old workspace concepts to current `ztlctl` concepts
- explain what was intentionally dropped
- explain what was restored via profiles/plugins
- explain what remains future work

**Acceptance criteria**

- a user familiar with `research` can understand `ztlctl`’s intended shape without reverse engineering the codebase

---

### ADP-002 — Evaluate migration/import tooling

**Status**
Completed with a documented no-go decision for now.

**Problem**
There is no first-class path from the old hybrid workspace into the new product, but this is not yet a top priority.

**Outcome**
Decide whether migration tooling is worth building after architecture stabilizes.

**Impact**
Low

**Effort**
S

**Dependencies**
ADP-001

**In scope**

- evaluate one-off import scripts versus no tooling
- estimate risk of importing old machine-layer assets
- estimate whether garden content should remain untouched and manual

**Acceptance criteria**

- a documented go/no-go decision exists
- if “go,” the scope is explicit and limited

## Public API, Interface, and Type Changes

The backlog assumes the following interface direction:

- add a new plugin hook such as `register_workspace_profiles()`
- add a new typed contract such as `WorkspaceProfileContribution`
- add a new config concept such as `[workspace].profile`
- deprecate using `[vault].client` as the long-term workspace-type selector
- update `init` and `workflow` to resolve profile choices dynamically
- keep `export ... --viewer` as a temporary rendering concern unless later moved into profile-owned export behavior
- remove any implied built-in `obsidian` plugin defaults that do not correspond to a real implementation

## Test Cases and Scenarios

- initializing a vault with no optional profile plugins installed still works
- initializing a vault with the official Obsidian profile installed produces the starter-kit assets and garden scaffold
- core init does not mutate `.obsidian/*` unless a selected profile owns that behavior
- broken profile plugins fail safely and do not block core CLI operations
- generated `self/identity.md` and `self/methodology.md` reflect current ID and lifecycle semantics
- garden directories are not indexed or mutated by core services by default
- profile discovery appears correctly in CLI help and interactive selection
- deprecation paths for existing `client` or hardcoded viewer assumptions are test-covered
- dashboard export remains useful both with and without the Obsidian profile installed

## Phase-Driven Approach

### Phase 0 — Establish Truth

**Items**

- ARC-001
- DRF-001
- DRF-002

**Goal**

Remove ambiguity before any architectural changes.

**Why first**

The repo currently mixes intended architecture with stale language and partial implementation. No profile or garden work should proceed until the current truth is documented.

**Exit criteria**

- hardcoded assumptions are fully inventoried
- generated self-docs no longer describe obsolete behavior
- design/doc drift is explicitly classified as fixed, intentional, or backlog

---

### Phase 1 — Lock the Architecture

**Items**

- ARC-002
- ARC-003
- GDN-002

**Goal**

Make the boundary decisions once, before coding.

**Why second**

Most later work depends on the decisions here:

- what is a profile
- what stays in core
- what `viewer` means
- what the machine/garden ownership boundary is

**Exit criteria**

- profile contract is documented
- deprecation path is defined
- machine/garden boundary is an explicit invariant

---

### Phase 2 — Upgrade Core to Support Profiles

**Items**

- PLG-001
- PLG-002
- PLG-003
- DRF-003

**Goal**

Make the architecture real in code.

**Why third**

This is the enabling layer for everything user-facing. Without it, Obsidian support will continue to accrete as special cases in core.

**Exit criteria**

- profile contributions are discoverable
- init/workflow use profiles instead of hardcoded workspace types
- core no longer owns Obsidian-specific scaffolding
- drift guard tests are in place

---

### Phase 3 — Ship the First-Party Obsidian Starter Kit

**Items**

- OBS-001
- OBS-002
- GDN-001

**Goal**

Restore a coherent hybrid workspace experience through the plugin ecosystem.

**Why fourth**

Only after the profile system exists should the first-party Obsidian experience be built.

**Exit criteria**

- the official Obsidian profile exists as a first-party profile/plugin
- it scaffolds `.obsidian` assets through the profile system
- it restores an explicit garden layer and templates

---

### Phase 4 — Harden the Hybrid Experience

**Items**

- OBS-003
- GDN-003

**Goal**

Clarify ownership of the shipped starter kit and keep hybrid workflow messaging coherent without adding profile lifecycle machinery.

**Why fifth**

Once the starter kit exists, the product still needs honest ownership language and coherent review/export framing. The previous assumption that ztlctl should validate and rewrite `.obsidian/` by default is no longer aligned with the intended direction.

**Exit criteria**

- docs and templates consistently describe `.obsidian/` as a one-shot scaffold
- review/export surfaces remain consistent with the restored hybrid model
- export is clearly described as an external review workbench rather than a vault-integrated workspace layer

---

### Phase 5 — Adoption and Legacy Follow-Through

**Items**

- ADP-001
- ADP-002

**Goal**

Document conceptual continuity with the old workspace without letting legacy concerns drive architecture.

**Why last**

This work becomes much easier and much more accurate after the new architecture is stable.

**Exit criteria**

- mapping guide exists
- migration/import tooling has a documented decision
- the documented decision is no-go for now unless product direction changes later

## Assumptions and Defaults

- hybrid machine-layer plus human-garden architecture is still desired
- Obsidian support should be delivered through the plugin ecosystem, not core special cases
- core should retain generic garden primitives such as maturity, garden backlog heuristics, and body-protection rules
- profile plugins should own concrete viewer/workspace UX, scaffolding, and `.obsidian` assets
- migration parity with the old `research` workspace is low priority
- the first Obsidian milestone should be a starter kit, not a deep live companion plugin
- garden content should remain outside core indexing and mutation paths by default
- spec and implementation drift should be treated as meaningful product debt, not background noise

## Implementation Notes

The intended execution order is:

1. establish truth about current hardcoded assumptions and drift
2. lock the profile architecture and ownership boundaries
3. upgrade core to support plugin-contributed workspace profiles
4. ship the first-party Obsidian starter kit through that profile system
5. harden the resulting hybrid experience
6. document adoption and legacy mapping last

Do not start with the Obsidian starter kit. Start with Phase 0.

## Important Changes or Additions to Public APIs, Interfaces, and Types

- `src/ztlctl/plugins/contracts.py`: add `WorkspaceProfileContribution`
- `src/ztlctl/plugins/hookspecs.py`: add `register_workspace_profiles`
- `src/ztlctl/plugins/manager.py`: add profile discovery, conflict handling, and retrieval
- `src/ztlctl/config/models.py`: add a workspace/profile setting and deprecate `vault.client` as the workspace-type source
- `src/ztlctl/commands/init_cmd.py` and `src/ztlctl/services/workflow.py`: resolve available profiles dynamically
- `src/ztlctl/services/init.py`: remove direct Obsidian scaffolding ownership from core

## Additional Test Cases and Scenarios

- no-profile path: new vault initializes successfully with a minimal default profile
- official-profile path: selecting the Obsidian profile creates profile-owned `.obsidian` assets and garden directories
- failure isolation: a broken profile plugin logs warnings and does not block vault init
- config compatibility: old `vault.client = "obsidian"` vaults still load with a warning and mapped behavior
- self-doc accuracy: generated `self/` documents mention real IDs, real maturity stages, and real commands
- ownership enforcement: core file discovery does not traverse `garden/` by default
- workflow compatibility: exported workflow assets still work whether or not the Obsidian profile is installed
- dashboard compatibility: dashboard export remains functional before and after the profile refactor

## Explicit Assumptions and Defaults Chosen

- use a first-party official Obsidian profile/plugin in the same repo/package initially, but make it consume the same public contract as any future third-party profile
- keep `viewer` only as a temporary render-target concept for export surfaces
- do not build a live Obsidian app/plugin transport in the first closure phases
- do not add new core content spaces for garden files; keep garden as a profile-owned human layer outside default core indexing
- do not let migration tooling block the architectural cleanup
