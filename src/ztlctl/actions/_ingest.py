"""Ingest ActionDefinition registrations."""

from __future__ import annotations


def _register_ingest_actions() -> None:
    """Register ingest ActionDefinitions."""
    from ztlctl.actions.definitions import ActionDefinition, ActionParam
    from ztlctl.actions.registry import get_action_registry

    # Lazy controller imports
    from ztlctl.controllers.ingest import IngestController

    registry = get_action_registry()

    registry.register(
        ActionDefinition(
            name="list_providers",
            description="List registered source providers.",
            category="ingest",
            params=(),
            handler=lambda vault, **kw: IngestController(vault).list_providers(**kw),
            side_effect="read",
            mcp_when_to_use="Before ingesting URLs or when diagnosing missing provider support.",
            mcp_avoid_when="You already know the provider you need and are ingesting text.",
            cli_group="ingest",
            cli_name="providers",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_text",
            description="Ingest raw text into a note or reference.",
            category="ingest",
            params=(
                ActionParam(
                    "title",
                    str,
                    required=True,
                    description="Title for the ingested artifact.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "body_text",
                    str,
                    required=True,
                    description="Raw text content to ingest.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_text(**kw),
            side_effect="write",
            mcp_when_to_use="Capturing external text or source material with provenance.",
            mcp_avoid_when="You are authoring a note or reference without source normalization.",
            mcp_common_errors=("VALIDATION_FAILED", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="text",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_file",
            description="Ingest a plain text or markdown file.",
            category="ingest",
            params=(
                ActionParam(
                    "path",
                    str,
                    required=True,
                    description="Filesystem path to the file to ingest.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "title",
                    str,
                    required=False,
                    default=None,
                    description="Optional title override for the ingested artifact.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_file(**kw),
            side_effect="write",
            mcp_when_to_use="Ingesting a local file into the vault.",
            mcp_avoid_when="You are ingesting a URL or raw text string.",
            mcp_common_errors=("NOT_FOUND", "VALIDATION_FAILED", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="file",
        )
    )

    registry.register(
        ActionDefinition(
            name="ingest_url",
            description="Ingest a URL through a registered source provider.",
            category="ingest",
            params=(
                ActionParam(
                    "url",
                    str,
                    required=True,
                    description="URL to ingest via a registered provider.",
                    cli_is_argument=True,
                ),
                ActionParam(
                    "provider",
                    str,
                    required=False,
                    default=None,
                    description="Optional provider name for URL ingestion.",
                ),
                ActionParam(
                    "title",
                    str,
                    required=False,
                    default=None,
                    description="Optional title override for the ingested artifact.",
                ),
                ActionParam(
                    "target_type",
                    str,
                    required=False,
                    default=None,
                    description="Destination artifact type: reference or note.",
                    choices=("reference", "note"),
                ),
                ActionParam(
                    "topic",
                    str,
                    required=False,
                    default=None,
                    description="Optional topic directory under notes/.",
                ),
                ActionParam(
                    "tags",
                    list,
                    required=False,
                    default=None,
                    description="Optional tags applied to the created artifact.",
                    cli_multiple=True,
                ),
                ActionParam(
                    "summary",
                    str,
                    required=False,
                    default=None,
                    description="Optional capture summary hint.",
                ),
                ActionParam(
                    "dry_run",
                    bool,
                    required=False,
                    default=False,
                    description="Preview normalized capture without writing files.",
                    cli_flag=True,
                ),
            ),
            handler=lambda vault, **kw: IngestController(vault).ingest_url(**kw),
            side_effect="write",
            mcp_when_to_use="Ingesting a web URL via a registered source provider.",
            mcp_avoid_when="You are ingesting raw text or a local file.",
            mcp_common_errors=("VALIDATION_FAILED", "NO_PROVIDER", "UNKNOWN_TYPE"),
            cli_group="ingest",
            cli_name="url",
        )
    )
