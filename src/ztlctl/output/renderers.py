"""Operation-specific Rich renderers for ServiceResult.

Each renderer writes to a Rich Console (backed by StringIO).  The caller
extracts the rendered text via ``get_output(console)``.

Renderers are dispatched by ``result.op`` in :func:`render_result`.
Unknown ops fall through to a generic key-value renderer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ztlctl.output.console import create_console, get_output, style_for_type

if TYPE_CHECKING:
    from rich.console import Console

    from ztlctl.services.result import ServiceResult


# ── Public API ────────────────────────────────────────────────────────


def render_result(result: ServiceResult, *, verbose: bool = False) -> str:
    """Render a ServiceResult to a styled string via Rich.

    Returns plain text (no ANSI) when Rich detects no terminal,
    which is the case inside Click's CliRunner and piped output.
    """
    console = create_console()

    if result.ok:
        renderer = _OP_RENDERERS.get(result.op, _render_generic)
        renderer(result, console, verbose=verbose)
    else:
        _render_error(result, console, verbose=verbose)

    return get_output(console).rstrip("\n")


def render_quiet(result: ServiceResult) -> str:
    """Render minimal output for ``--quiet`` mode."""
    if not result.ok:
        msg = result.error.message if result.error else "Unknown error"
        return f"ERROR: {result.op} — {msg}"

    # For table/list results, return IDs only
    items = result.data.get("items") or result.data.get("communities")
    if items and isinstance(items, list):
        return "\n".join(_extract_id(item) for item in items if _extract_id(item))

    return f"OK: {result.op}"


# ── Helpers ───────────────────────────────────────────────────────────


def _extract_id(item: Any) -> str:
    """Extract an ID from a dict item (items, steps, communities, etc.)."""
    if isinstance(item, dict):
        for key in ("id", "community_id"):
            val = item.get(key)
            if val is not None:
                return str(val)
        return ""
    return ""


def _status_line(console: Console, result: ServiceResult) -> None:
    """Print the OK/ERROR status line."""
    label = Text("OK", style="ztl.ok")
    op = Text(f"  {result.op}", style="ztl.op")
    console.print(label, op, end="")
    console.print()


def _field(console: Console, key: str, value: Any) -> None:
    """Print a single indented key-value field."""
    k = Text(f"  {key}: ", style="ztl.key")
    if key == "id" or key.endswith("_id"):
        v = Text(str(value), style="ztl.id")
    elif key == "path":
        v = Text(str(value), style="ztl.path")
    elif key == "title":
        v = Text(str(value), style="ztl.title")
    else:
        v = Text(str(value))
    console.print(k, v, end="")
    console.print()


def _render_meta(console: Console, result: ServiceResult) -> None:
    """Print meta block including telemetry span tree (verbose only)."""
    if not result.meta:
        return

    console.print()
    console.print(Text("  meta:", style="dim"))

    for k, v in result.meta.items():
        if k == "telemetry":
            _render_telemetry_tree(console, v, indent=4)
        else:
            console.print(f"    {k}: {v}")


def _render_telemetry_tree(
    console: Console,
    span_data: dict[str, Any],
    indent: int = 4,
) -> None:
    """Render a hierarchical span tree with color-coded timing."""
    prefix = " " * indent
    name = span_data.get("name", "?")
    duration = span_data.get("duration_ms", 0.0)

    if duration > 1000:
        style = "bold red"
    elif duration > 100:
        style = "yellow"
    else:
        style = "dim"

    line = f"{prefix}[{style}]{duration:>8.2f}ms[/{style}]  {name}"

    extras: list[str] = []
    if span_data.get("tokens"):
        extras.append(f"tokens={span_data['tokens']}")
    if span_data.get("cost"):
        extras.append(f"cost={span_data['cost']}")
    if span_data.get("annotations"):
        for ak, av in span_data["annotations"].items():
            extras.append(f"{ak}={av}")
    if extras:
        line += f"  ({', '.join(extras)})"

    console.print(line)

    for child in span_data.get("children", []):
        _render_telemetry_tree(console, child, indent=indent + 4)


def _item_table(
    items: list[dict[str, Any]],
    *,
    score_key: str | None = None,
    extra_columns: list[str] | None = None,
    verbose: bool = False,
) -> Table:
    """Build a Rich Table for a list of content items."""
    table = Table(show_header=True, show_lines=False, pad_edge=False, expand=False)
    table.add_column("ID", style="ztl.id", no_wrap=True)
    table.add_column("Title", style="ztl.title")
    table.add_column("Type")
    table.add_column("Status")

    if score_key:
        table.add_column(score_key.replace("_", " ").title(), style="ztl.score", justify="right")

    for col in extra_columns or []:
        table.add_column(col.replace("_", " ").title())

    if verbose:
        table.add_column("Modified", style="dim")

    for item in items:
        row: list[str] = [
            str(item.get("id", "")),
            str(item.get("title", "")),
            str(item.get("type", "")),
            str(item.get("status", "")),
        ]
        if score_key:
            val = item.get(score_key, item.get("constraint", item.get("centrality", "")))
            row.append(f"{float(val):.4f}" if isinstance(val, (int, float)) else str(val))
        for col in extra_columns or []:
            row.append(str(item.get(col, "")))
        if verbose:
            row.append(str(item.get("modified", "")))
        table.add_row(*row)

    return table


# ── Error renderer ────────────────────────────────────────────────────


def _render_error(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    err = result.error
    msg = err.message if err else "Unknown error"
    label = Text("ERROR", style="ztl.error")
    op = Text(f"  {result.op}", style="ztl.op")
    sep = Text(" — ")
    console.print(label, op, sep, msg)

    if verbose and err and err.detail:
        console.print(Text("  detail:", style="dim"))
        for k, v in err.detail.items():
            console.print(f"    {k}: {v}")


# ── Mutation renderers ────────────────────────────────────────────────


def _render_mutation(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render create/update/archive/session-start/reopen/rollback results."""
    _status_line(console, result)
    mutation_keys = (
        "id",
        "session_id",
        "path",
        "title",
        "type",
        "status",
        "backup_file",
        "restored_from",
    )
    for key in mutation_keys:
        if key in result.data:
            _field(console, key, result.data[key])
    # Show fields_changed for update ops
    if "fields_changed" in result.data:
        _field(console, "fields_changed", result.data["fields_changed"])
    if verbose:
        _render_meta(console, result)


def _render_batch(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render create_batch results."""
    _status_line(console, result)
    created = result.data.get("created", [])
    errors = result.data.get("errors", [])
    _field(console, "created", len(created))
    _field(console, "errors", len(errors))

    if created and verbose:
        console.print()
        table = _item_table(created, verbose=False)
        console.print(table)

    for err in errors:
        idx = err.get("index")
        msg = err.get("error")
        console.print(f"  [ztl.error]error[/ztl.error] index={idx}: {msg}")


# ── Query renderers ───────────────────────────────────────────────────


def _render_single_item(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render query-get result as a panel with metadata."""
    d = result.data
    # Metadata lines
    lines: list[str] = []
    for key in ("type", "subtype", "status", "topic", "session", "created", "modified"):
        val = d.get(key)
        if val is not None:
            lines.append(f"{key}: {val}")

    tags = d.get("tags", [])
    if tags:
        lines.append(f"tags: {', '.join(tags)}")

    # Links
    links_out = d.get("links_out", [])
    links_in = d.get("links_in", [])
    if links_out:
        targets = [f"{lnk['id']} ({lnk['edge_type']})" for lnk in links_out]
        lines.append(f"links out: {', '.join(targets)}")
    if links_in:
        sources = [f"{lnk['id']} ({lnk['edge_type']})" for lnk in links_in]
        lines.append(f"links in: {', '.join(sources)}")

    content = "\n".join(lines)
    body = d.get("body", "")
    if body:
        content += f"\n\n{body.strip()}"

    title = f"{d.get('id', '?')} — {d.get('title', 'Untitled')}"
    style = style_for_type(str(d.get("type", "")))
    console.print(Panel(content, title=title, border_style=style or "dim", expand=False))


def _render_item_table(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render search or list_items results as a table."""
    items = result.data.get("items", [])
    score_key = "score" if result.op == "search" else None
    if score_key is None and items and "score" in items[0]:
        score_key = "score"
    table = _item_table(items, score_key=score_key, verbose=verbose)
    console.print(table)
    console.print(f"\n{result.data.get('count', len(items))} items")


def _render_work_queue(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render work_queue with priority coloring."""
    items = result.data.get("items", [])
    table = Table(show_header=True, show_lines=False, pad_edge=False, expand=False)
    table.add_column("ID", style="ztl.id", no_wrap=True)
    table.add_column("Title", style="ztl.title")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Impact")
    table.add_column("Effort")
    table.add_column("Score", style="ztl.score", justify="right")
    if verbose:
        table.add_column("Modified", style="dim")

    priority_styles = {"critical": "bold red", "high": "yellow", "medium": "", "low": "dim"}

    for item in items:
        p = str(item.get("priority", "medium"))
        p_styled = Text(p, style=priority_styles.get(p, ""))
        row: list[Any] = [
            str(item.get("id", "")),
            str(item.get("title", "")),
            str(item.get("status", "")),
            p_styled,
            str(item.get("impact", "")),
            str(item.get("effort", "")),
            f"{item.get('score', 0):.2f}",
        ]
        if verbose:
            row.append(str(item.get("modified", "")))
        table.add_row(*row)

    console.print(table)
    console.print(f"\n{result.data.get('count', len(items))} tasks")


def _render_decision_support(
    result: ServiceResult, console: Console, *, verbose: bool = False
) -> None:
    """Render decision_support with three sections."""
    d = result.data
    counts = d.get("counts", {})
    topic = d.get("topic") or "(all topics)"
    console.print(f"Decision support for [ztl.title]{topic}[/ztl.title]")
    console.print(
        f"  {counts.get('decisions', 0)} decisions, "
        f"{counts.get('notes', 0)} notes, "
        f"{counts.get('references', 0)} references"
    )

    sections = [
        ("decisions", "Decisions"),
        ("notes", "Notes"),
        ("references", "References"),
    ]
    for section, label in sections:
        items = d.get(section, [])
        if items:
            console.print(f"\n[bold]{label}[/bold]")
            table = _item_table(items, verbose=verbose)
            console.print(table)


# ── Graph renderers ───────────────────────────────────────────────────


def _render_scored_table(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render related, rank, gaps, bridges as scored tables."""
    items = result.data.get("items", [])
    # Determine score column name from op
    score_cols: dict[str, str] = {
        "related": "score",
        "rank": "score",
        "gaps": "constraint",
        "bridges": "centrality",
    }
    score_key = score_cols.get(result.op, "score")
    extra = ["depth"] if result.op == "related" else []
    table = _item_table(items, score_key=score_key, extra_columns=extra, verbose=verbose)
    console.print(table)

    source = result.data.get("source_id")
    if source:
        console.print(f"\nSource: [ztl.id]{source}[/ztl.id]")
    console.print(f"{result.data.get('count', len(items))} results")


def _render_themes(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render community detection results."""
    communities = result.data.get("communities", [])
    console.print(f"[bold]{result.data.get('count', len(communities))} communities[/bold]")

    for community in communities:
        cid = community.get("community_id", "?")
        size = community.get("size", 0)
        console.print(f"\n[bold]Community {cid}[/bold] ({size} members)")
        for member in community.get("members", []):
            style = style_for_type(str(member.get("type", "")))
            mid = member.get("id", "")
            title = member.get("title", "")
            console.print(f"  [ztl.id]{mid}[/ztl.id]  [{style}]{title}[/{style}]")


def _render_path(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render shortest path as a chain."""
    steps = result.data.get("steps", [])
    length = result.data.get("length", 0)

    if not steps:
        console.print("No path found.")
        return

    chain_parts: list[str] = []
    for step in steps:
        sid = step.get("id", "?")
        title = step.get("title", "Untitled")
        chain_parts.append(f"[ztl.id]{sid}[/ztl.id] ({title})")

    console.print(" → ".join(chain_parts))
    console.print(f"\nPath length: {length}")


# ── Check renderers ───────────────────────────────────────────────────


def _render_check(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render check results with issues grouped by category."""
    issues = result.data.get("issues", [])
    count = result.data.get("count", len(issues))

    if count == 0:
        console.print("[ztl.ok]OK[/ztl.ok]  No issues found.")
        return

    severity_styles = {"error": "ztl.error", "warning": "ztl.warning"}

    # Group by category
    by_category: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        cat = str(issue.get("category", "unknown"))
        by_category.setdefault(cat, []).append(issue)

    for cat, cat_issues in by_category.items():
        console.print(f"\n[bold]{cat}[/bold]")
        for issue in cat_issues:
            sev = str(issue.get("severity", "warning"))
            style = severity_styles.get(sev, "")
            msg = issue.get("message", "")
            node_id = issue.get("node_id")
            prefix = f"[{style}]{sev}[/{style}]" if style else sev
            nid = f" [{node_id}]" if node_id else ""
            console.print(f"  {prefix}{nid}: {msg}")
            if verbose and issue.get("fix_action"):
                console.print(f"    fix: {issue['fix_action']}")

    errors = sum(1 for i in issues if i.get("severity") == "error")
    warnings = count - errors
    console.print(f"\n{errors} errors, {warnings} warnings")


def _render_fix(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render fix results."""
    _status_line(console, result)
    fixes = result.data.get("fixes", [])
    _field(console, "fixes_applied", result.data.get("count", len(fixes)))
    if verbose:
        for fix in fixes:
            console.print(f"  - {fix}")


def _render_rebuild(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render rebuild results."""
    _status_line(console, result)
    for key in ("nodes_indexed", "edges_created", "tags_found", "nodes_materialized"):
        if key in result.data:
            _field(console, key, result.data[key])


def _render_materialize(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render materialize_metrics results."""
    _status_line(console, result)
    _field(console, "nodes_updated", result.data.get("nodes_updated", 0))


# ── Session renderers ─────────────────────────────────────────────────


def _render_session_close(
    result: ServiceResult, console: Console, *, verbose: bool = False
) -> None:
    """Render session close with enrichment summary."""
    _status_line(console, result)
    d = result.data
    for key in ("session_id", "status"):
        if key in d:
            _field(console, key, d[key])
    # Enrichment counts
    for key in ("reweave_count", "orphan_count", "integrity_issues"):
        val = d.get(key)
        if val is not None:
            _field(console, key, val)
    if verbose:
        _render_meta(console, result)


def _render_cost(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render session cost/budget results."""
    _status_line(console, result)
    d = result.data
    _field(console, "session_id", d["session_id"])
    _field(console, "total_cost", d["total_cost"])
    _field(console, "entry_count", d["entry_count"])
    if "budget" in d:
        _field(console, "budget", d["budget"])
        remaining = d["remaining"]
        _field(console, "remaining", remaining)
        over = d.get("over_budget", False)
        if over:
            console.print("  [ztl.error]OVER BUDGET[/ztl.error]")


def _render_context(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render agent context assembly results."""
    _status_line(console, result)
    d = result.data
    _field(console, "total_tokens", d["total_tokens"])
    _field(console, "budget", d["budget"])
    _field(console, "remaining", d["remaining"])
    _field(console, "pressure", d["pressure"])
    if verbose:
        layers = d.get("layers", {})
        console.print()
        console.print(Text("  layers:", style="dim"))
        for layer_name, layer_data in layers.items():
            if isinstance(layer_data, list):
                console.print(f"    {layer_name}: {len(layer_data)} items")
            elif isinstance(layer_data, dict):
                console.print(f"    {layer_name}: dict")
            elif layer_data is None:
                console.print(f"    {layer_name}: (empty)")
            else:
                console.print(f"    {layer_name}: present")
        _render_meta(console, result)


def _render_brief(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render agent brief orientation."""
    _status_line(console, result)
    d = result.data

    # Session info
    session_info = d.get("session")
    if session_info:
        _field(console, "session_id", session_info["session_id"])
        _field(console, "topic", session_info["topic"])
        _field(console, "status", session_info["status"])
    else:
        console.print("  [dim]No active session[/dim]")

    # Vault stats
    vault_stats = d.get("vault_stats", {})
    if vault_stats:
        console.print()
        table = Table(show_header=True, show_lines=False, pad_edge=False, expand=False)
        table.add_column("Type")
        table.add_column("Count", justify="right")
        for node_type, count in sorted(vault_stats.items()):
            table.add_row(node_type, str(count))
        console.print(table)

    # Recent decisions
    decisions = d.get("recent_decisions", [])
    if decisions:
        console.print(f"\n  {len(decisions)} recent decisions")

    # Work queue
    wq_count = d.get("work_queue_count", 0)
    if wq_count:
        console.print(f"  {wq_count} actionable tasks")


# ── Reweave renderers ────────────────────────────────────────────────


def _render_reweave(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render reweave or prune results."""
    d = result.data
    is_dry = d.get("dry_run", False)

    _status_line(console, result)
    if is_dry:
        console.print("  [ztl.warning]DRY RUN[/ztl.warning]")

    target = d.get("target_id")
    if target:
        _field(console, "target_id", target)
    _field(console, "count", d.get("count", 0))

    # Show suggestions (dry run) or connected/pruned (real)
    items = d.get("suggestions") or d.get("connected") or d.get("pruned") or d.get("stale") or []
    if items:
        has_score = any("score" in i for i in items)
        if has_score:
            table = Table(show_header=True, show_lines=False, pad_edge=False, expand=False)
            table.add_column("ID", style="ztl.id")
            table.add_column("Title", style="ztl.title")
            table.add_column("Score", style="ztl.score", justify="right")
            for item in items:
                table.add_row(
                    str(item.get("id", "")),
                    str(item.get("title", "")),
                    f"{item.get('score', 0):.4f}",
                )
            console.print(table)
        else:
            for item in items:
                console.print(f"  [ztl.id]{item.get('id', '')}[/ztl.id]  {item.get('title', '')}")

    if verbose:
        _render_meta(console, result)


def _render_undo(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render undo results."""
    _status_line(console, result)
    undone = result.data.get("undone", [])
    _field(console, "count", result.data.get("count", len(undone)))

    if undone:
        table = Table(show_header=True, show_lines=False, pad_edge=False, expand=False)
        table.add_column("Log ID", justify="right")
        table.add_column("Source", style="ztl.id")
        table.add_column("Target", style="ztl.id")
        table.add_column("Action")
        table.add_column("Reversed")
        for u in undone:
            table.add_row(
                str(u.get("log_id", "")),
                str(u.get("source_id", "")),
                str(u.get("target_id", "")),
                str(u.get("action", "")),
                str(u.get("reversed", "")),
            )
        console.print(table)


# ── Init renderers ───────────────────────────────────────────────────


def _render_init(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render init_vault results with vault details and file manifest."""
    _status_line(console, result)
    d = result.data
    for key in ("vault_path", "name", "client", "tone"):
        if key in d:
            _field(console, key, d[key])
    topics = d.get("topics", [])
    if topics:
        _field(console, "topics", ", ".join(topics))
    files = d.get("files_created", [])
    _field(console, "files_created", len(files))
    if verbose:
        for f in files:
            console.print(f"    {f}")
        _render_meta(console, result)


# ── Export renderers ─────────────────────────────────────────────────


def _render_export(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render export results with output path and counts."""
    _status_line(console, result)
    d = result.data
    for key in ("output_dir", "output_file", "format"):
        if key in d:
            _field(console, key, d[key])
    for key in ("file_count", "node_count", "edge_count"):
        if key in d:
            _field(console, key, d[key])
    files = d.get("files_created", [])
    if files:
        _field(console, "files_created", len(files))
        if verbose:
            for f in files:
                console.print(f"    {f}")
    if verbose:
        _render_meta(console, result)


# ── Upgrade renderers ────────────────────────────────────────────────


def _render_upgrade(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Render upgrade/migration results."""
    _status_line(console, result)
    d = result.data
    if "applied_count" in d:
        _field(console, "applied_count", d["applied_count"])
    if "pending_count" in d:
        _field(console, "pending_count", d["pending_count"])
    if "current" in d:
        _field(console, "current", d["current"])
    if "head" in d:
        _field(console, "head", d["head"])
    if "backup_path" in d:
        _field(console, "backup_path", d["backup_path"])
    if "message" in d:
        _field(console, "message", d["message"])
    if verbose and d.get("pending"):
        console.print()
        for p in d["pending"]:
            console.print(f"  {p['revision']}: {p['description']}")


# ── Generic fallback ──────────────────────────────────────────────────


def _render_generic(result: ServiceResult, console: Console, *, verbose: bool = False) -> None:
    """Fallback renderer: status line + all data as key-value pairs."""
    _status_line(console, result)
    for key, value in result.data.items():
        if isinstance(value, (dict, list)):
            import json as _json

            _field(console, key, _json.dumps(value, separators=(",", ":")))
        else:
            _field(console, key, value)
    if verbose:
        _render_meta(console, result)


# ── Dispatch table ────────────────────────────────────────────────────

_OP_RENDERERS: dict[str, Any] = {
    # Mutations
    "create_note": _render_mutation,
    "create_reference": _render_mutation,
    "create_task": _render_mutation,
    "create_batch": _render_batch,
    "update": _render_mutation,
    "archive": _render_mutation,
    "supersede": _render_mutation,
    "rollback": _render_mutation,
    # Query
    "get": _render_single_item,
    "search": _render_item_table,
    "list_items": _render_item_table,
    "work_queue": _render_work_queue,
    "decision_support": _render_decision_support,
    # Graph
    "related": _render_scored_table,
    "rank": _render_scored_table,
    "gaps": _render_scored_table,
    "bridges": _render_scored_table,
    "themes": _render_themes,
    "path": _render_path,
    "materialize_metrics": _render_materialize,
    # Check
    "check": _render_check,
    "fix": _render_fix,
    "rebuild": _render_rebuild,
    # Session
    "session_start": _render_mutation,
    "session_close": _render_session_close,
    "session_reopen": _render_mutation,
    "log_entry": _render_mutation,
    "cost": _render_cost,
    "context": _render_context,
    "brief": _render_brief,
    "extract_decision": _render_mutation,
    # Reweave
    "reweave": _render_reweave,
    "prune": _render_reweave,
    "undo": _render_undo,
    # Init
    "init_vault": _render_init,
    "regenerate_self": _render_mutation,
    "check_staleness": _render_generic,
    # Export
    "export_markdown": _render_export,
    "export_indexes": _render_export,
    "export_graph": _render_export,
    # Upgrade
    "upgrade": _render_upgrade,
}
