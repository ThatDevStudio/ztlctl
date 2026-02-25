"""AppContext — shared Click context for all commands.

Created once by the root CLI group and flows to all subcommands via
``@click.pass_obj``.  Provides lazy Vault initialization and centralized
result emission (stdout/stderr routing + exit codes).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.output.formatters import OutputSettings, format_result

if TYPE_CHECKING:
    from ztlctl.config.settings import ZtlSettings
    from ztlctl.infrastructure.vault import Vault
    from ztlctl.services.result import ServiceResult


class AppContext:
    """Shared context flowing through Click's command hierarchy.

    Subcommands access it via ``@click.pass_obj``.  The vault is lazily
    initialized on first use so ``--help`` and ``--version`` never
    trigger database access.
    """

    def __init__(self, settings: ZtlSettings) -> None:
        self.settings = settings
        self._vault: Vault | None = None

    @property
    def vault(self) -> Vault:
        """The vault instance (created lazily on first access)."""
        if self._vault is None:
            from ztlctl.infrastructure.vault import Vault

            self._vault = Vault(self.settings)
            self._vault.init_event_bus(sync=self.settings.sync)
        return self._vault

    def emit(self, result: ServiceResult) -> None:
        """Format and output a ServiceResult with correct exit semantics.

        * Success (``result.ok``): writes to stdout, returns normally.
          Warnings are emitted to stderr so they don't pollute piped output.
        * Failure: writes to stderr, exits with code 1.
        """
        settings = OutputSettings(
            json_output=self.settings.json_output,
            quiet=self.settings.quiet,
            verbose=self.settings.verbose,
        )
        output = format_result(result, settings=settings)
        if result.ok:
            click.echo(output)
            # In JSON mode, warnings are already in the serialized payload.
            if not settings.json_output:
                for warning in result.warnings:
                    click.echo(f"WARNING: {warning}", err=True)
        else:
            click.echo(output, err=True)
            raise SystemExit(1)
