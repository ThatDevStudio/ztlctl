# API Reference

Auto-generated from Python source using [mkdocstrings](https://mkdocstrings.github.io/python/).
All signatures and docstrings reflect the current `src/ztlctl/` codebase.

!!! note "Scope"
    This reference covers the **plugin public API** only — the contracts, hookspecs, and action system
    that plugin authors and advanced integrators interact with. Internal service and infrastructure
    layers are not documented here.

## Plugin Hookspecs

The `ZtlctlHookSpec` class defines all pluggy hookspecs. Implement any subset of these in your plugin class.

::: ztlctl.plugins.hookspecs
    options:
      show_root_heading: true
      heading_level: 3
      members_order: source
      show_source: true
      show_signature_annotations: true
      separate_signature: true
      filters:
        - "!^_"

## Plugin Contracts

Data classes returned from and passed to hookspecs.

::: ztlctl.plugins.contracts
    options:
      show_root_heading: true
      heading_level: 3
      members_order: source
      show_source: false
      show_signature_annotations: true

## API Versioning

::: ztlctl.plugins._version
    options:
      show_root_heading: true
      heading_level: 3
      show_source: false
      members_order: source
      filters:
        - "!^_COMPATIBILITY"

## Action System

`ActionDefinition` and `ActionParam` are the frozen dataclasses that describe every registered action.
Plugin authors use these when implementing `register_note_types()` — PluginManager auto-creates
`ActionDefinition` instances for each `NoteTypeDefinition` returned.

::: ztlctl.actions.definitions
    options:
      show_root_heading: true
      heading_level: 3
      show_source: false
      show_signature_annotations: true

::: ztlctl.actions.registry
    options:
      show_root_heading: true
      heading_level: 3
      show_source: false
      show_signature_annotations: true
      filters:
        - "!^_"
