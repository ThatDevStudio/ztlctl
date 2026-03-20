"""Plugin discovery, loading, and contribution collection."""

from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, TypeVar

import pluggy

from ztlctl.plugins._version import PluginLoadError, check_plugin_api_version
from ztlctl.plugins.contracts import (
    CliCommandContribution,
    McpPromptContribution,
    McpResourceContribution,
    McpToolContribution,
    RenderContribution,
    SourceProviderContribution,
    VaultInitStepContribution,
    WorkflowModuleContribution,
    WorkspaceProfileContribution,
)
from ztlctl.plugins.hookspecs import ZtlctlHookSpec

PROJECT_NAME = "ztlctl"

logger = logging.getLogger(__name__)
_ContributionT = TypeVar("_ContributionT")


class PluginManager:
    """Manages plugin discovery, loading, and hook dispatch."""

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager(PROJECT_NAME)
        self._pm.add_hookspecs(ZtlctlHookSpec)
        self._loaded: bool = False

    def discover_and_load(
        self,
        *,
        local_dir: Path | None = None,
        include_entrypoints: bool = True,
    ) -> list[str]:
        """Discover plugins from entry points and an optional local directory.

        Uses pluggy's native setuptools entry_point discovery for the
        ``ztlctl.plugins`` group when *include_entrypoints* is true, then
        scans *local_dir* (typically ``.ztlctl/plugins/``) for single-file
        Python plugins.

        Returns a list of loaded plugin names.
        """
        if include_entrypoints:
            self._pm.load_setuptools_entrypoints("ztlctl.plugins")
            self._normalize_plugin_instances()
        if local_dir is not None:
            self._discover_local(local_dir)
        self._register_content_models()
        self._register_note_types()
        self._loaded = True
        return self.list_plugin_names()

    def register_plugin(self, plugin: object, name: str | None = None) -> None:
        """Register a plugin instance directly (e.g. built-in plugins).

        Performs an API version check before completing registration.
        Incompatible plugins are not registered and a warning is logged.
        """
        resolved_name = name or plugin.__class__.__name__
        self._pm.register(plugin, name=resolved_name)

        # Version check — unregister if incompatible, warn if deprecated.
        try:
            warnings = check_plugin_api_version(plugin, resolved_name)
        except PluginLoadError as exc:
            logger.warning("Skipping incompatible plugin %s: %s", resolved_name, exc)
            self._pm.unregister(plugin)
            return
        for warning in warnings:
            logger.warning(warning)

        if self._loaded:
            self._register_plugin_content_models(plugin, resolved_name)
        logger.debug("Registered plugin: %s", resolved_name)

    def unregister(self, plugin: object) -> None:
        """Unregister a plugin instance."""
        self._pm.unregister(plugin)

    @property
    def is_loaded(self) -> bool:
        """Whether discover_and_load() has been called."""
        return self._loaded

    @property
    def hook(self) -> pluggy.HookRelay:
        """Access the hook relay for dispatching events."""
        return self._pm.hook

    def get_plugins(self) -> list[object]:
        """Return all registered plugins."""
        return list(self._pm.get_plugins())

    def list_plugin_names(self) -> list[str]:
        """Return names of all registered plugins."""
        return [self._pm.get_name(p) or p.__class__.__name__ for p in self._pm.get_plugins()]

    def cli_command_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[CliCommandContribution]:
        """Collect plugin CLI command contributions."""
        return self._collect_contributions(
            "register_cli_commands",
            CliCommandContribution,
            key_fn=lambda item: item.name,
            reserved=reserved_names,
        )

    def mcp_tool_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[McpToolContribution]:
        """Collect plugin MCP tool contributions."""
        return self._collect_contributions(
            "register_mcp_tools",
            McpToolContribution,
            key_fn=lambda item: item.name,
            reserved=reserved_names,
        )

    def mcp_resource_contributions(
        self,
        *,
        reserved_uris: set[str] | None = None,
    ) -> list[McpResourceContribution]:
        """Collect plugin MCP resource contributions."""
        return self._collect_contributions(
            "register_mcp_resources",
            McpResourceContribution,
            key_fn=lambda item: item.uri,
            reserved=reserved_uris,
        )

    def mcp_prompt_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[McpPromptContribution]:
        """Collect plugin MCP prompt contributions."""
        return self._collect_contributions(
            "register_mcp_prompts",
            McpPromptContribution,
            key_fn=lambda item: item.name,
            reserved=reserved_names,
        )

    def workflow_module_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[WorkflowModuleContribution]:
        """Collect plugin workflow module contributions."""
        return self._collect_contributions(
            "register_workflow_modules",
            WorkflowModuleContribution,
            key_fn=lambda item: item.name,
            reserved=reserved_names,
        )

    def workspace_profile_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[WorkspaceProfileContribution]:
        """Collect plugin workspace profile contributions."""
        return self._collect_contributions(
            "register_workspace_profiles",
            WorkspaceProfileContribution,
            key_fn=lambda item: item.profile_id,
            reserved=reserved_names,
        )

    def vault_init_step_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[VaultInitStepContribution]:
        """Collect plugin vault init step contributions."""
        return self._collect_contributions(
            "register_vault_init_steps",
            VaultInitStepContribution,
            key_fn=lambda item: item.step_id,
            reserved=reserved_names,
        )

    def source_provider_contributions(
        self,
        *,
        reserved_names: set[str] | None = None,
    ) -> list[SourceProviderContribution]:
        """Collect plugin source provider contributions."""
        return self._collect_contributions(
            "register_source_providers",
            SourceProviderContribution,
            key_fn=lambda item: item.name,
            reserved=reserved_names,
        )

    def render_contributions(
        self,
        *,
        reserved_types: set[str] | None = None,
    ) -> list[RenderContribution]:
        """Collect plugin render contributions for custom note types (PLUG-06)."""
        return self._collect_contributions(
            "register_render_contributions",
            RenderContribution,
            key_fn=lambda item: item.note_type,
            reserved=reserved_types,
        )

    def inject_configs(self, settings: Any) -> None:
        """Validate and inject per-plugin configuration (PLUG-03).

        Iterates all registered plugins, calls ``get_config_schema`` if
        present to retrieve a Pydantic model class, looks up the matching
        ``[plugins.<name>]`` section from *settings.plugins*, validates the
        raw dict against the schema, and passes the result to ``initialize``.

        If validation fails the plugin receives ``initialize(config=None)``
        and a warning is logged. Plugins without ``get_config_schema`` or
        ``initialize`` are silently skipped.

        Args:
            settings: A :class:`~ztlctl.config.settings.ZtlSettings` instance
                (typed as Any to avoid a circular import).
        """
        self._inject_plugin_configs(settings)

    def _inject_plugin_configs(self, settings: Any) -> None:
        """Internal implementation of per-plugin config injection."""
        from pydantic import ValidationError

        plugins_cfg = getattr(settings, "plugins", None)

        for plugin in self._pm.get_plugins():
            plugin_name = self._pm.get_name(plugin) or plugin.__class__.__name__

            get_schema_fn = getattr(plugin, "get_config_schema", None)
            initialize_fn = getattr(plugin, "initialize", None)

            if initialize_fn is None:
                continue

            schema_cls = None
            if get_schema_fn is not None:
                try:
                    schema_cls = get_schema_fn()
                except Exception:
                    logger.warning(
                        "Plugin %s raised in get_config_schema",
                        plugin_name,
                        exc_info=True,
                    )

            raw_config: dict[str, Any] = {}
            if plugins_cfg is not None:
                get_fn = getattr(plugins_cfg, "get_plugin_config", None)
                if get_fn is not None:
                    raw_config = get_fn(plugin_name) or {}

            validated_config = None
            if schema_cls is not None and raw_config:
                try:
                    validated_config = schema_cls(**raw_config)
                except (ValidationError, TypeError) as exc:
                    logger.warning(
                        "Plugin %s config validation failed; calling initialize(config=None): %s",
                        plugin_name,
                        exc,
                    )
                    validated_config = None
            elif schema_cls is not None and not raw_config:
                # Schema declared but no TOML section — pass None
                validated_config = None

            try:
                initialize_fn(config=validated_config)
            except Exception:
                logger.warning(
                    "Plugin %s raised in initialize",
                    plugin_name,
                    exc_info=True,
                )

    # ------------------------------------------------------------------
    # Local directory discovery
    # ------------------------------------------------------------------

    def _discover_local(self, local_dir: Path) -> None:
        """Scan *local_dir* for single-file Python plugins.

        Each ``*.py`` file (excluding ``_``-prefixed names) is loaded as a
        module. Classes inside the module that carry pluggy hookimpl-decorated
        methods are instantiated and registered.

        Errors are logged as warnings but never raised — a broken local plugin
        must not prevent the rest of the system from starting.
        """
        if not local_dir.is_dir():
            return

        for py_file in sorted(local_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"ztlctl_local_plugin_{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    logger.warning("Could not create module spec for %s", py_file)
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except Exception:
                logger.warning("Failed to load local plugin %s", py_file, exc_info=True)
                # Clean up partial module registration
                sys.modules.pop(module_name, None)
                continue

            # Scan module for classes that have hookimpl-decorated methods
            for _attr_name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module_name:
                    continue  # skip imported classes
                if not self._has_hook_impls(obj):
                    continue
                try:
                    instance = obj()
                    self.register_plugin(instance, name=module_name)
                    logger.debug(
                        "Loaded local plugin %s from %s",
                        obj.__name__,
                        py_file,
                    )
                except Exception:
                    logger.warning(
                        "Failed to instantiate plugin class %s from %s",
                        obj.__name__,
                        py_file,
                        exc_info=True,
                    )

    def _normalize_plugin_instances(self) -> None:
        """Replace registered plugin classes with instantiated objects.

        Entry-point loading may register a plugin class directly. Hook dispatch
        against class objects leaves ``self`` unbound and fails at runtime.
        """
        for plugin in list(self._pm.get_plugins()):
            if not inspect.isclass(plugin):
                continue
            if not self._has_hook_impls(plugin):
                continue

            plugin_name = self._pm.get_name(plugin) or plugin.__name__
            self._pm.unregister(plugin)

            try:
                instance = plugin()
            except Exception:
                logger.warning(
                    "Failed to instantiate entry-point plugin %s",
                    plugin_name,
                    exc_info=True,
                )
                continue

            # API version check before accepting the instance.
            try:
                version_warnings = check_plugin_api_version(instance, plugin_name)
            except PluginLoadError as exc:
                logger.warning(
                    "Skipping incompatible entry-point plugin %s: %s",
                    plugin_name,
                    exc,
                )
                continue
            for warning in version_warnings:
                logger.warning(warning)

            self._pm.register(instance, name=plugin_name)
            logger.debug("Instantiated entry-point plugin: %s", plugin_name)

    def _register_note_types(
        self,
        *,
        note_registry: Any = None,
        action_registry: Any = None,
    ) -> None:
        """Register plugin-contributed NoteTypeDefinitions and auto-create ActionDefinitions.

        Iterates all results from ``register_note_types`` hooks, registers each
        :class:`~ztlctl.domain.registry.NoteTypeDefinition` into the
        :class:`~ztlctl.domain.registry.NoteTypeRegistry` singleton (or a
        provided test registry), and auto-creates ``create_*``, ``update_*``,
        ``close_*`` ActionDefinitions into the ActionRegistry.

        Duplicate registrations are logged as warnings and skipped — they do
        not raise.

        Args:
            note_registry: Override NoteTypeRegistry for testing. Defaults to
                the module-level singleton.
            action_registry: Override ActionRegistry for testing. Defaults to
                the module-level singleton.
        """
        from ztlctl.domain.registry import NoteTypeDefinition, get_note_type_registry

        if note_registry is None:
            note_registry = get_note_type_registry()
        if action_registry is None:
            from ztlctl.actions.registry import get_action_registry

            action_registry = get_action_registry()

        try:
            hook_results = self._pm.hook.register_note_types()
        except Exception:
            logger.warning("Failed to collect note type registrations from plugins", exc_info=True)
            return

        for plugin_items in hook_results:
            if plugin_items is None:
                continue
            if not isinstance(plugin_items, list):
                logger.warning("register_note_types returned non-list value; skipping")
                continue
            for item in plugin_items:
                if not isinstance(item, NoteTypeDefinition):
                    logger.warning(
                        "register_note_types returned non-NoteTypeDefinition item %r; skipping",
                        item,
                    )
                    continue
                try:
                    note_registry.register(item)
                except ValueError:
                    logger.warning(
                        "Skipping duplicate note type registration %r from plugin",
                        item.name,
                    )
                    continue
                self._register_note_type_actions(item, action_registry=action_registry)

    def _register_note_type_actions(
        self,
        ntd: Any,
        *,
        action_registry: Any = None,
    ) -> None:
        """Auto-create create/update/close ActionDefinitions for a plugin note type.

        Each :class:`~ztlctl.domain.registry.NoteTypeDefinition` registered by
        a plugin gets three corresponding ActionDefinitions so the CLI and MCP
        generators pick them up automatically without any extra plugin code.

        Args:
            ntd: The NoteTypeDefinition to create actions for.
            action_registry: Override ActionRegistry for testing.
        """
        from ztlctl.actions.definitions import ActionDefinition, ActionParam

        if action_registry is None:
            from ztlctl.actions.registry import get_action_registry

            action_registry = get_action_registry()

        ntd_name: str = ntd.name
        content_type: str = ntd.content_type

        # Common params for create action
        create_params = (
            ActionParam(
                name="title",
                type=str,
                required=True,
                description=f"Title of the {ntd_name}",
            ),
            ActionParam(
                name="tags",
                type=list,
                required=False,
                default=None,
                description="Comma-separated tags",
                cli_multiple=True,
            ),
            ActionParam(
                name="links",
                type=list,
                required=False,
                default=None,
                description="IDs or titles to link to",
                cli_multiple=True,
            ),
            ActionParam(
                name="body",
                type=str,
                required=False,
                default=None,
                description=f"Body content for the {ntd_name}",
            ),
        )

        # Params for update action
        update_params = (
            ActionParam(
                name="content_id",
                type=str,
                required=True,
                description=f"ID of the {ntd_name} to update",
            ),
            ActionParam(
                name="title",
                type=str,
                required=False,
                default=None,
                description="New title",
            ),
            ActionParam(
                name="tags",
                type=list,
                required=False,
                default=None,
                description="New tags",
                cli_multiple=True,
            ),
            ActionParam(
                name="body",
                type=str,
                required=False,
                default=None,
                description="New body content",
            ),
            ActionParam(
                name="status",
                type=str,
                required=False,
                default=None,
                description="New status",
            ),
        )

        # Params for close action
        close_params = (
            ActionParam(
                name="content_id",
                type=str,
                required=True,
                description=f"ID of the {ntd_name} to close",
            ),
            ActionParam(
                name="summary",
                type=str,
                required=False,
                default=None,
                description="Closing summary",
            ),
        )

        def _make_create_handler(nt: str, ct: str) -> Any:
            _note_type = nt
            _content_type = ct

            def _handler(vault: Any, **kwargs: Any) -> Any:
                from ztlctl.controllers.create import CreateController

                ctrl = CreateController(vault)
                title: str = kwargs.pop("title", "")
                # Route to the correct controller method based on content_type.
                # kwargs content varies by runtime call; use Any-typed dispatch.
                if _content_type == "task":
                    return ctrl.create_task(title, **kwargs)
                if _content_type == "reference":
                    return ctrl.create_reference(title, subtype=_note_type, **kwargs)
                # Default: treat as note
                return ctrl.create_note(title, subtype=_note_type, **kwargs)

            return _handler

        def _make_update_handler(nt: str) -> Any:
            def _handler(vault: Any, **kwargs: Any) -> Any:
                from ztlctl.controllers.update import UpdateController

                return UpdateController(vault).update(**kwargs)

            return _handler

        def _make_close_handler(nt: str) -> Any:
            def _handler(vault: Any, **kwargs: Any) -> Any:
                from ztlctl.controllers.update import UpdateController

                return UpdateController(vault).archive(**kwargs)

            return _handler

        actions = [
            ActionDefinition(
                name=f"create_{ntd_name}",
                description=f"Create a new {ntd_name}",
                category="creation",
                params=create_params,
                handler=_make_create_handler(ntd_name, content_type),
                side_effect="write",
                cli_group=content_type,
                cli_name=ntd_name,
                mcp_when_to_use=(f"Use when the user wants to create a new {ntd_name}."),
            ),
            ActionDefinition(
                name=f"update_{ntd_name}",
                description=f"Update an existing {ntd_name}",
                category="mutation",
                params=update_params,
                handler=_make_update_handler(ntd_name),
                side_effect="write",
                cli_group=content_type,
                cli_name=f"update-{ntd_name}",
                mcp_when_to_use=(f"Use when the user wants to update a {ntd_name}."),
            ),
            ActionDefinition(
                name=f"close_{ntd_name}",
                description=f"Close a {ntd_name}",
                category="mutation",
                params=close_params,
                handler=_make_close_handler(ntd_name),
                side_effect="write",
                cli_group=content_type,
                cli_name=f"close-{ntd_name}",
                mcp_when_to_use=(f"Use when the user wants to close or archive a {ntd_name}."),
            ),
        ]

        for action in actions:
            try:
                action_registry.register(action)
            except ValueError:
                logger.warning(
                    "Skipping duplicate action registration %r for note type %r",
                    action.name,
                    ntd_name,
                )

    def _register_content_models(self) -> None:
        """Load plugin-provided content subtype models into the domain registry."""
        for plugin in self._pm.get_plugins():
            plugin_name = self._pm.get_name(plugin) or plugin.__class__.__name__
            self._register_plugin_content_models(plugin, plugin_name)

    @staticmethod
    def _register_plugin_content_models(plugin: object, plugin_name: str) -> None:
        """Register content models exposed by a single plugin instance."""
        from ztlctl.domain.content import register_content_model

        hook = getattr(plugin, "register_content_models", None)
        if hook is None:
            return

        try:
            model_map = hook()
        except Exception:
            logger.warning(
                "Failed to collect content models from plugin %s",
                plugin_name,
                exc_info=True,
            )
            return

        if model_map is None:
            return
        if not isinstance(model_map, dict):
            logger.warning(
                "Plugin %s returned non-dict content model registrations",
                plugin_name,
            )
            return

        for subtype_name, model_cls in model_map.items():
            try:
                register_content_model(subtype_name, model_cls)
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping content model registration %r from plugin %s",
                    subtype_name,
                    plugin_name,
                    exc_info=True,
                )

    @staticmethod
    def _has_hook_impls(cls: type) -> bool:
        """Check whether *cls* has any methods decorated with ``@hookimpl``.

        Pluggy's ``HookimplMarker("ztlctl")`` sets a ``ztlctl_impl``
        attribute on decorated methods.
        """
        for name in dir(cls):
            if name.startswith("_"):
                continue
            method = getattr(cls, name, None)
            if callable(method) and getattr(method, "ztlctl_impl", None):
                return True
        return False

    def _collect_contributions(
        self,
        hook_name: str,
        expected_type: type[_ContributionT],
        *,
        key_fn: Any,
        reserved: set[str] | None = None,
    ) -> list[_ContributionT]:
        """Collect typed plugin contributions from one hook."""
        if not self._loaded:
            return []

        hook = getattr(self._pm.hook, hook_name, None)
        if hook is None:
            return []

        reserved_keys = set(reserved or ())
        seen = set(reserved_keys)
        results: list[_ContributionT] = []

        try:
            hook_results = hook()
        except Exception:
            logger.warning("Failed to collect contributions from %s", hook_name, exc_info=True)
            return []

        for plugin_items in hook_results:
            if plugin_items is None:
                continue
            if not isinstance(plugin_items, list):
                logger.warning("%s returned non-list contributions", hook_name)
                continue
            for item in plugin_items:
                if not isinstance(item, expected_type):
                    logger.warning(
                        "Skipping invalid %s contribution: expected %s",
                        hook_name,
                        expected_type.__name__,
                    )
                    continue
                key = key_fn(item)
                if key in reserved_keys:
                    logger.warning(
                        "Skipping reserved plugin contribution %r from %s", key, hook_name
                    )
                    continue
                if key in seen:
                    logger.warning(
                        "Skipping duplicate plugin contribution %r from %s", key, hook_name
                    )
                    continue
                seen.add(key)
                results.append(item)

        return results
