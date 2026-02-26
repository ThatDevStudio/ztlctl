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

        # Configure structured logging
        from ztlctl.config.logging import configure_logging

        configure_logging(verbose=settings.verbose, log_json=settings.log_json)

        # Enable telemetry context var when verbose
        if settings.verbose:
            from ztlctl.services.telemetry import enable_telemetry

            enable_telemetry()

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

    def log_action_cost(self, result: ServiceResult, cost: int) -> None:
        """Log action cost to the active session.

        Called after emit() for commands that accept ``--cost``.
        No-op if cost is 0 or no active session exists. Failures are
        silently ignored — cost logging never blocks the primary command.
        """
        if cost <= 0:
            return
        try:
            from ztlctl.services.session import SessionService

            content_id = result.data.get("id", "") if result.data else ""
            summary = f"{result.op}: {content_id}" if content_id else result.op
            SessionService(self.vault).log_entry(
                summary,
                cost=cost,
                entry_type="action_cost",
                references=[content_id] if content_id else None,
            )
        except Exception:
            pass  # Cost logging never blocks
