"""ActionParam and ActionDefinition frozen dataclasses.

ActionParam is a single-source-of-truth parameter descriptor that captures
all metadata needed to auto-generate CLI options, MCP tool parameters, and
interactive prompts.

ActionDefinition is a frozen descriptor for one operation in the system.
All controller methods are registered as ActionDefinitions, enabling
auto-generation of CLI and MCP surfaces.

Both dataclasses are frozen for thread safety and hashability.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

# ---------------------------------------------------------------------------
# ActionParam
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionParam:
    """One parameter descriptor — single source of truth for CLI and MCP.

    Fields
    ------
    name
        Parameter name (e.g. ``"query"``, ``"limit"``).
    type
        Python built-in type: ``str``, ``int``, ``bool``, ``list[str]``.
    required
        Whether the parameter is required. Defaults to ``True``.
    default
        Default value when not required. Defaults to ``None``.
    description
        Human-readable description for CLI help and MCP docs.
    choices
        Tuple of valid string choices (used for Click ``choice`` type and
        MCP enum). ``None`` means unrestricted.
    cli_multiple
        When ``True``, the CLI option accepts multiple values (``--tag x --tag y``).
    cli_is_argument
        When ``True``, rendered as a Click positional argument instead of
        an option.
    cli_flag
        When ``True``, rendered as a boolean Click flag (``--verbose``).
    mcp_example
        Example value shown in MCP tool docs (``"find notes about python"``).
    """

    name: str
    type: type
    required: bool = True
    default: Any = None
    description: str = ""
    choices: tuple[str, ...] | None = None
    cli_multiple: bool = False
    cli_is_argument: bool = False
    cli_flag: bool = False
    mcp_example: str = ""


# ---------------------------------------------------------------------------
# ActionDefinition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionDefinition:
    """One operation in the system. Frozen for thread safety and hashability.

    All controller methods are registered as ActionDefinitions.  The
    define-once model allows CLI and MCP surfaces to be auto-generated
    from this single descriptor.

    Fields
    ------
    name
        Unique dotted name (e.g. ``"note.search"``, ``"note.create"``).
    description
        Human-readable description of what this action does.
    category
        Logical category for grouping (e.g. ``"query"``, ``"create"``,
        ``"graph"``).
    params
        Tuple of :class:`ActionParam` descriptors in argument order.
    handler
        Callable that performs the action; returns a ``ServiceResult``.
        Typed as ``Callable[..., Any]`` to avoid circular imports.
    side_effect
        ``"read"`` for non-mutating operations; ``"write"`` for mutating.

    MCP-specific metadata
    ---------------------
    mcp_when_to_use
        Guidance for the agent about when to invoke this action.
    mcp_avoid_when
        Guidance for the agent about when *not* to invoke this action.
    mcp_common_errors
        Tuple of common error messages that callers should handle.

    CLI-specific metadata
    ---------------------
    cli_group
        Click command group name (``None`` means top-level).
    cli_examples
        Example CLI invocations shown in ``--help`` output.
    cli_interactive_params
        Param names to prompt interactively when ``--interactive`` is set.

    Presentation
    ------------
    custom_presentation
        Escape hatch for actions with complex output that can't be
        rendered by the generic presenter.
    """

    # Core identity
    name: str
    description: str
    category: str
    params: tuple[ActionParam, ...]
    handler: Callable[..., Any]
    side_effect: Literal["read", "write"]

    # MCP-specific metadata
    mcp_when_to_use: str = ""
    mcp_avoid_when: str = ""
    mcp_common_errors: tuple[str, ...] = ()

    # CLI-specific metadata
    cli_group: str | None = None
    cli_examples: str = ""
    cli_interactive_params: tuple[str, ...] = ()

    # Presentation escape hatch
    custom_presentation: bool = False
