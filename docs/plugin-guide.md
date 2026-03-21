# Plugin Authoring Guide

ztlctl's plugin system is built on [pluggy](https://pluggy.readthedocs.io/). Plugins hook into lifecycle events, extend the CLI and MCP server, contribute custom note types, and declare security capabilities. Plugins are discovered automatically at startup via Python entry points (`importlib.metadata`).

This guide covers:

1. [Tutorial: Build Your First Plugin](#tutorial-build-your-first-plugin) — step-by-step walkthrough
2. [Hookspec Reference](#hookspec-reference) — all 16 active hookspecs with exact signatures and behavior
3. [Plugin Metadata](#plugin-metadata-pluginmetadata) — marketplace and discoverability metadata
4. [Compatibility and Versioning](#compatibility-and-versioning) — API version contract

---

## Tutorial: Build Your First Plugin

### 1. Create the Plugin Package

Create a minimal Python package:

```
my_vault_plugin/
    __init__.py
pyproject.toml
```

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-vault-plugin"
version = "0.1.0"
dependencies = [
    "pluggy>=1.3",
    "pydantic>=2.0",
]
```

In `my_vault_plugin/__init__.py`, import the hook marker:

```python
import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")
```

All hook implementations must be decorated with `@hookimpl`. The marker name must be `"ztlctl"` to match the hook specification namespace.

### 2. Add PLUGIN_API_VERSION

Declare the API version your plugin targets at class level:

```python
class MyVaultPlugin:
    PLUGIN_API_VERSION = 1
```

The current host API version is `1`. Plugins declaring `PLUGIN_API_VERSION = 1` are fully compatible. See [Compatibility and Versioning](#compatibility-and-versioning) for the compatibility window rules.

Missing `PLUGIN_API_VERSION` is allowed — legacy plugins load without a warning but receive no compatibility guarantees.

### 3. Implement post_action

`post_action` is the primary hook for reacting to vault events. All registered plugins receive every call; filter on `action_name` to scope your plugin's logic:

```python
import pluggy
from typing import Any

hookimpl = pluggy.HookimplMarker("ztlctl")


class MyVaultPlugin:
    PLUGIN_API_VERSION = 1

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        if action_name != "create_note":
            return

        # result is the ServiceResult object (or None on the EventBus bridge path)
        if result is not None and (not hasattr(result, "ok") or not result.ok):
            return  # skip failed actions

        content_id = kwargs.get("content_id", "")
        title = kwargs.get("title", "")
        print(f"New note created: [{content_id}] {title}")
```

Common `action_name` values:

| Action Name | Triggered by |
|---|---|
| `create_note` | `ztlctl create note` |
| `create_reference` | `ztlctl create reference` |
| `create_task` | `ztlctl create task` |
| `update` | `ztlctl update` |
| `close` / `archive` | `ztlctl close` / `ztlctl archive` |
| `session_start` | `ztlctl session start` |
| `session_close` | `ztlctl session close` |
| `reweave` | `ztlctl reweave` |
| `check` | `ztlctl check` |
| `init` | `ztlctl init` |

### 4. Declare Capabilities

Plugins that access sensitive resources must declare their capabilities:

```python
@hookimpl
def declare_capabilities(self) -> set[str]:
    return {"network"}
```

Valid capability identifiers:

| Capability | Meaning |
|---|---|
| `filesystem` | Reads or writes files outside the vault |
| `network` | Makes outbound network requests |
| `database` | Directly accesses the vault SQLite database |
| `git` | Runs git subprocess commands |

The PluginManager emits a warning if a plugin uses a capability without declaring it. In a future API version, undeclared capabilities may be blocked.

### 5. Add a Custom Note Type (NoteTypeDefinition)

Plugins can register entirely new note types with their own lifecycle, template, and required structure:

```python
from ztlctl.domain.content import NoteModel
from ztlctl.domain.registry import NoteTypeDefinition


class MyVaultPlugin:
    PLUGIN_API_VERSION = 1

    @hookimpl
    def register_note_types(self) -> list[NoteTypeDefinition]:
        sprint_type = NoteTypeDefinition(
            name="sprint",
            content_type="note",
            model_cls=NoteModel,
            transitions={
                "active": ["completed", "cancelled"],
                "completed": [],
                "cancelled": [],
            },
            template_name="sprint.md.j2",
            required_sections=["## Goal", "## Stories"],
        )
        return [sprint_type]
```

`NoteTypeDefinition` fields:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unique registry key (e.g. `"sprint"`) |
| `content_type` | `str` | Parent type: `"note"`, `"reference"`, `"task"`, or `"log"` |
| `model_cls` | `type[ContentModel]` | Pydantic model class for validation |
| `transitions` | `dict[str, list[str]]` | Status transition map; every target must also be a key |
| `template_name` | `str` | Jinja2 template filename (empty string for DB-only types) |
| `required_sections` | `list[str]` | Markdown sections required during validation |
| `initial_status` | `str` | Status on creation; empty means "use first key of transitions" |
| `is_subtype` | `bool` | `True` for subtypes of existing content types |
| `parent_type` | `str \| None` | Required when `is_subtype=True` |

PluginManager auto-creates `create`, `update`, and `close` ActionDefinitions for each registered `NoteTypeDefinition` and adds them to the ActionRegistry. The CLI and MCP generators pick them up automatically.

### 6. Add Plugin Config (get_config_schema + initialize)

Plugins can declare a Pydantic config schema so users configure the plugin in `.ztlctl/config.toml`:

```python
from pydantic import BaseModel


class MyPluginConfig(BaseModel):
    webhook_url: str = ""
    enabled: bool = True


class MyVaultPlugin:
    PLUGIN_API_VERSION = 1

    def __init__(self) -> None:
        self._config = MyPluginConfig()

    @hookimpl
    def get_config_schema(self) -> type[BaseModel]:
        return MyPluginConfig

    @hookimpl
    def initialize(self, config: BaseModel | None) -> None:
        if config is not None:
            self._config = config  # type: ignore[assignment]
```

Matching section in `.ztlctl/config.toml`:

```toml
[plugins.my-plugin]
webhook_url = "https://hooks.example.com/ztlctl"
enabled = true
```

`get_config_schema()` is called once at plugin load time. If a matching `[plugins.<name>]` TOML section exists, its contents are validated against the returned model and then passed to `initialize()`. If no config section exists, `initialize()` receives `None`.

### 7. Register via Entry Point

Register the plugin class using a Python entry point in `pyproject.toml`:

```toml
[project.entry-points."ztlctl.plugins"]
my-plugin = "my_vault_plugin:MyVaultPlugin"
```

ztlctl discovers all plugins registered under the `ztlctl.plugins` entry-point group using `importlib.metadata` at startup. The entry-point name (here `my-plugin`) is used as the plugin's config section name and display name. Install the package (`pip install -e .`) and ztlctl will load it automatically.

### 8. Test Your Plugin

Plugins can be tested directly without a running vault:

```python
import pytest
from my_vault_plugin import MyVaultPlugin


def test_post_action_create_note(capsys: pytest.CaptureFixture[str]) -> None:
    plugin = MyVaultPlugin()

    # Simulate a successful create_note action
    plugin.post_action(
        action_name="create_note",
        kwargs={"content_id": "20240101120000", "title": "My First Note"},
        result=None,  # None = pass-through on the EventBus bridge path
    )

    captured = capsys.readouterr()
    assert "20240101120000" in captured.out
    assert "My First Note" in captured.out


def test_post_action_ignores_other_actions() -> None:
    plugin = MyVaultPlugin()

    # Should be a no-op for other action names
    plugin.post_action(
        action_name="reweave",
        kwargs={},
        result=None,
    )
    # No assertion needed — just verify no exception is raised
```

Hooks can be tested without pluggy infrastructure by calling them directly as methods. Use `result=None` to simulate the EventBus bridge path (pass-through).

---

## Complete MyVaultPlugin Example

```python
"""my_vault_plugin/__init__.py — complete working example."""

from __future__ import annotations

from typing import Any

import pluggy
from pydantic import BaseModel

from ztlctl.domain.content import NoteModel
from ztlctl.domain.registry import NoteTypeDefinition

hookimpl = pluggy.HookimplMarker("ztlctl")


class MyPluginConfig(BaseModel):
    webhook_url: str = ""
    enabled: bool = True


class MyVaultPlugin:
    """Example ztlctl plugin demonstrating core plugin patterns."""

    PLUGIN_API_VERSION = 1

    def __init__(self) -> None:
        self._config = MyPluginConfig()

    # ── Security ──────────────────────────────────────────────────────────

    @hookimpl
    def declare_capabilities(self) -> set[str]:
        return {"network"}

    # ── Configuration ─────────────────────────────────────────────────────

    @hookimpl
    def get_config_schema(self) -> type[BaseModel]:
        return MyPluginConfig

    @hookimpl
    def initialize(self, config: BaseModel | None) -> None:
        if config is not None:
            self._config = config  # type: ignore[assignment]

    # ── Lifecycle events ──────────────────────────────────────────────────

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        if action_name != "create_note":
            return
        if result is not None and (not hasattr(result, "ok") or not result.ok):
            return

        if not self._config.enabled or not self._config.webhook_url:
            return

        content_id = kwargs.get("content_id", "")
        title = kwargs.get("title", "")
        print(f"Webhook: new note [{content_id}] {title} -> {self._config.webhook_url}")

    # ── Custom note types ─────────────────────────────────────────────────

    @hookimpl
    def register_note_types(self) -> list[NoteTypeDefinition]:
        return [
            NoteTypeDefinition(
                name="sprint",
                content_type="note",
                model_cls=NoteModel,
                transitions={
                    "active": ["completed", "cancelled"],
                    "completed": [],
                    "cancelled": [],
                },
                template_name="sprint.md.j2",
                required_sections=["## Goal", "## Stories"],
            )
        ]
```

`pyproject.toml` for the complete plugin:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-vault-plugin"
version = "0.1.0"
dependencies = ["pluggy>=1.3", "pydantic>=2.0"]

[project.entry-points."ztlctl.plugins"]
my-plugin = "my_vault_plugin:MyVaultPlugin"

[tool.ztlctl-plugin]
name = "my-vault-plugin"
version = "0.1.0"
author = "Your Name"
description = "Example ztlctl plugin"
ztlctl_api_version = 1
capabilities = ["network"]
```

---

## Hookspec Reference

All 16 active hookspecs are defined in the `ZtlctlHookSpec` class in `src/ztlctl/plugins/hookspecs.py`. Implement only the hooks your plugin needs — unimplemented hooks are no-ops. See also the [API Reference](api-reference.md) for auto-generated signatures and docstrings.

Every implementation must be decorated with:

```python
import pluggy
hookimpl = pluggy.HookimplMarker("ztlctl")
```

---

### Generic Action Hooks (Preferred)

These two hooks cover the full action lifecycle. Prefer them over the deprecated per-event hooks.

#### `pre_action`

```python
def pre_action(
    self, action_name: str, kwargs: dict[str, Any]
) -> ActionRejection | dict[str, Any] | None:
    ...
```

- `firstresult=True` — the first plugin returning a non-`None` value wins; subsequent plugins are not called
- Return `ActionRejection(reason=..., code=..., detail={})` to abort the action before it runs
- Return a modified `kwargs` dict to transform inputs before the action handler runs
- Return `None` (or do not implement) to pass through unchanged
- Fires before every registered action

`ActionRejection` fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `reason` | `str` | — | Human-readable rejection explanation |
| `code` | `str` | `"plugin_rejected"` | Machine-readable error code |
| `detail` | `dict[str, Any]` | `{}` | Optional structured context |

Example — rate-limit note creation:

```python
from ztlctl.plugins.contracts import ActionRejection

@hookimpl
def pre_action(
    self, action_name: str, kwargs: dict[str, Any]
) -> ActionRejection | dict[str, Any] | None:
    if action_name == "create_note" and self._rate_limit_exceeded():
        return ActionRejection(
            reason="Rate limit exceeded — too many notes created today",
            code="rate_limit_exceeded",
            detail={"limit": 50},
        )
    return None
```

#### `post_action`

```python
def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
    ...
```

- `firstresult=False` — all registered plugins receive this call
- Called after every action regardless of outcome
- Filter on `action_name` to scope your plugin's behavior
- `result` is the `ServiceResult` object, or `None` on the EventBus bridge path
- Return value is ignored

---

### Plugin Lifecycle Hooks

#### `get_config_schema`

```python
def get_config_schema(self) -> type[BaseModel] | None:
    ...
```

- `firstresult=True`
- Return a Pydantic `BaseModel` **class** (not an instance) to declare the plugin's config schema
- Called once at plugin load time
- Return `None` or do not implement if the plugin needs no configuration

#### `initialize`

```python
def initialize(self, config: BaseModel | None) -> None:
    ...
```

- Called once after `get_config_schema()`, with the validated config instance (or `None` if no config)
- Store the config reference on `self` for use in other hooks
- If `get_config_schema()` returns `None`, `config` will always be `None`

---

### Extension Contribution Hooks

These hooks let plugins add content to various ztlctl subsystems. All are `firstresult=False` — every plugin's contributions are collected and merged.

| Hook | Return Type | What It Contributes |
|---|---|---|
| `register_content_models` | `dict[str, type[ContentModel]] \| None` | Subtype-to-ContentModel mappings added to `CONTENT_REGISTRY` |
| `register_cli_commands` | `list[CliCommandContribution] \| None` | Additional Click commands exposed under `ztlctl` |
| `register_mcp_tools` | `list[McpToolContribution] \| None` | MCP tool handlers available via `ztlctl serve` |
| `register_mcp_resources` | `list[McpResourceContribution] \| None` | MCP resource URIs available via `ztlctl serve` |
| `register_mcp_prompts` | `list[McpPromptContribution] \| None` | MCP prompt templates available via `ztlctl serve` |
| `register_workflow_modules` | `list[WorkflowModuleContribution] \| None` | Workflow export module renderers |
| `register_workspace_profiles` | `list[WorkspaceProfileContribution] \| None` | Workspace profile definitions for `ztlctl init` |
| `register_vault_init_steps` | `list[VaultInitStepContribution] \| None` | Ordered steps injected into the `ztlctl init` pipeline |
| `register_source_providers` | `list[SourceProviderContribution] \| None` | Source acquisition providers for content ingestion |
| `register_note_types` | `list[NoteTypeDefinition] \| None` | Custom note types with lifecycle and CRUD auto-generation |
| `register_render_contributions` | `list[RenderContribution] \| None` | Rich terminal and MCP formatters for custom note types |

Return `None` (or do not implement) to contribute nothing.

#### Contribution Contract Types

Contribution dataclasses live in `ztlctl.plugins.contracts`:

**`CliCommandContribution`**

```python
@dataclass(frozen=True)
class CliCommandContribution:
    name: str
    command: click.Command
```

**`McpToolContribution`**

```python
@dataclass(frozen=True)
class McpToolContribution:
    name: str
    handler: Callable[..., dict[str, Any]]
    catalog_entry: ToolCatalogEntry
```

**`McpResourceContribution`**

```python
@dataclass(frozen=True)
class McpResourceContribution:
    uri: str
    description: str
    handler: Callable[[Any], Any]
```

**`McpPromptContribution`**

```python
@dataclass(frozen=True)
class McpPromptContribution:
    name: str
    description: str
    handler: Callable[..., str]
    takes_vault: bool = True
```

**`WorkflowModuleContribution`**

```python
@dataclass(frozen=True)
class WorkflowModuleContribution:
    name: str
    render: Callable[[dict[str, Any]], str]
```

**`WorkspaceProfileContribution`**

```python
@dataclass(frozen=True)
class WorkspaceProfileContribution:
    profile_id: str
    description: str
    aliases: tuple[str, ...] = ()
    managed_paths: tuple[str, ...] = ()
    init_scaffold: Callable[[Path], list[str]] | None = None
```

**`VaultInitStepContribution`**

```python
@dataclass(frozen=True)
class VaultInitStepContribution:
    step_id: str
    description: str
    run: Callable[[VaultInitContext], VaultInitStepResult]
    order: int = 500
    profiles: tuple[str, ...] = ()
```

Steps with lower `order` run first. `profiles` restricts the step to named workspace profiles; empty tuple means the step runs for all profiles.

**`SourceProviderContribution`**

```python
@dataclass(frozen=True)
class SourceProviderContribution:
    name: str
    description: str
    schemes: tuple[str, ...]
    fetch: Callable[[SourceFetchRequest], SourceFetchResult]
```

**`RenderContribution`**

```python
@dataclass(frozen=True)
class RenderContribution:
    note_type: str
    rich_formatter: Callable[[dict[str, Any]], str]
    mcp_formatter: Callable[[dict[str, Any]], dict[str, Any]]
```

---

### Security — Capability Declarations

#### `declare_capabilities`

```python
def declare_capabilities(self) -> set[str] | None:
    ...
```

Return the set of capabilities this plugin uses:

```python
@hookimpl
def declare_capabilities(self) -> set[str]:
    return {"filesystem", "network"}
```

Valid values: `{"filesystem", "network", "database", "git"}`.

Return `None` or do not implement to indicate no declaration. Missing declarations generate a warning in plugin API v2. Future API versions may enforce declarations and refuse to load undeclared plugins.

---

### Deprecated Per-Event Hooks

!!! warning "Deprecated Hookspecs"
    The following hookspecs still work but are deprecated since plugin API v2. Use `pre_action` / `post_action` instead:

    - `post_create`, `post_update`, `post_close`, `post_reweave`
    - `post_session_start`, `post_session_close`
    - `post_check`, `post_init`, `post_init_profile`

    These emit `DeprecationWarning` when implemented and will be removed in a future API version.

The following hooks are deprecated since plugin API v2. They emit `DeprecationWarning` when implemented. Use `post_action` with `action_name` filtering instead.

| Deprecated Hook | Signature | Migrate to |
|---|---|---|
| `post_create` | `(content_type: str, content_id: str, title: str, path: str, tags: list[str]) -> None` | `post_action` + filter `action_name in {"create_note", "create_reference", "create_task", "create_log"}` |
| `post_update` | `(content_type: str, content_id: str, fields_changed: list[str], path: str) -> None` | `post_action` + filter `action_name.startswith("update_")` |
| `post_close` | `(content_type: str, content_id: str, path: str, summary: str) -> None` | `post_action` + filter `action_name.endswith("_close")` |
| `post_reweave` | `(source_id: str, affected_ids: list[str], links_added: int) -> None` | `post_action` + filter `action_name == "reweave"` |
| `post_session_start` | `(session_id: str) -> None` | `post_action` + filter `action_name == "session_start"` |
| `post_session_close` | `(session_id: str, stats: dict[str, Any]) -> None` | `post_action` + filter `action_name == "session_close"` |
| `post_check` | `(issues_found: int, issues_fixed: int) -> None` | `post_action` + filter `action_name == "check"` |
| `post_init` | `(vault_name: str, client: str, tone: str) -> None` | `post_action` + filter `action_name == "init"` |
| `post_init_profile` | `(vault_name: str, profile: str, tone: str, managed_paths: list[str]) -> None` | `post_action` + filter `action_name == "init_profile"` |

These hooks will be removed in a future API version. Migration is straightforward: replace per-event implementations with a single `post_action` and filter by `action_name`.

---

## Plugin Metadata (PluginMetadata)

For marketplace listing and future discoverability, declare plugin metadata in `pyproject.toml`:

```toml
[tool.ztlctl-plugin]
name = "my-vault-plugin"
version = "1.0.0"
author = "Your Name"
description = "What this plugin does"
ztlctl_api_version = 1
capabilities = ["network"]
```

This corresponds to the `PluginMetadata` dataclass in `ztlctl.plugins.contracts`:

```python
@dataclass(frozen=True)
class PluginMetadata:
    name: str
    version: str
    author: str
    capabilities: tuple[str, ...]
    ztlctl_api_version: int
    description: str = ""
```

Note: `capabilities` in `PluginMetadata` refers to contribution hook identifiers (e.g. `"register_note_types"`, `"register_cli_commands"`), not security capability identifiers like `"network"`. Use `declare_capabilities()` for security declarations and `PluginMetadata.capabilities` for feature surface declarations.

---

## Compatibility and Versioning

| Item | Value |
|---|---|
| Current `PLUGIN_API_VERSION` | `1` |
| Compatibility window | `2` (versions within 2 of current load with a deprecation warning) |
| Minimum supported version | `PLUGIN_API_VERSION - window` (exclusive) |

**Rules:**

- `PLUGIN_API_VERSION = 1` (current): fully compatible, loads without warning
- Plugin version within the window but below current: loads with a deprecation warning
- Plugin version equal to or below the compatibility floor (`current - window`): rejected with `PluginLoadError`
- Plugin version above `PLUGIN_API_VERSION`: rejected with `PluginLoadError` ("please upgrade ztlctl")
- No `PLUGIN_API_VERSION` attribute: treated as a legacy plugin; loads without warning but receives no compatibility guarantees

Example with current API version `1` and window `2`:

| Plugin declares | Result |
|---|---|
| `PLUGIN_API_VERSION = 1` | Loads, no warning |
| `PLUGIN_API_VERSION = 2` | Rejected — plugin requires a newer host |
| No attribute | Loads, no warning (legacy) |

```python
# Compatibility check logic (simplified from _version.py)
from ztlctl.plugins._version import PLUGIN_API_VERSION, PluginLoadError

COMPATIBILITY_WINDOW = 2

declared = getattr(plugin, "PLUGIN_API_VERSION", None)
if declared is None:
    pass  # legacy — allowed
elif declared > PLUGIN_API_VERSION:
    raise PluginLoadError("Plugin requires newer ztlctl version")
elif declared <= PLUGIN_API_VERSION - COMPATIBILITY_WINDOW:
    raise PluginLoadError("Plugin API version too old — update the plugin")
elif declared < PLUGIN_API_VERSION:
    print("Warning: plugin is within compatibility window but not current")
```
