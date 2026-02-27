"""Shared Jinja2 template loading with per-vault override support."""

from __future__ import annotations

from pathlib import Path

from jinja2 import BaseLoader, ChoiceLoader, Environment, FileSystemLoader, PackageLoader


def build_template_environment(group: str, *, vault_root: Path | None = None) -> Environment:
    """Build a Jinja2 environment with user overrides before packaged defaults.

    User overrides are loaded from ``.ztlctl/templates/`` inside the vault.
    Both a namespaced directory (for example ``.ztlctl/templates/content/``)
    and the shared root are supported so templates can be organized without
    breaking the simpler flat override layout.
    """

    loaders: list[BaseLoader] = []
    if vault_root is not None:
        template_root = vault_root / ".ztlctl" / "templates"
        loaders.append(FileSystemLoader([str(template_root / group), str(template_root)]))

    loaders.append(PackageLoader("ztlctl", f"templates/{group}"))
    return Environment(loader=ChoiceLoader(loaders), keep_trailing_newline=True)
