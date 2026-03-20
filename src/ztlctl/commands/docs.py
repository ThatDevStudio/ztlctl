"""Command group: docs search (custom_presentation — --json flag requires hand-written command)."""

from __future__ import annotations

import click


@click.group("docs", help="Search ztlctl documentation.")
def docs_group() -> None:
    pass


@docs_group.command("search")
@click.argument("query")
@click.option(
    "--limit",
    default=5,
    show_default=True,
    help="Maximum number of results.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output results as JSON.",
)
def docs_search(query: str, limit: int, json_output: bool) -> None:
    """Search the ztlctl documentation corpus."""
    from ztlctl.services.docs import _docs_search_impl

    results = _docs_search_impl(query, limit=limit)

    # Handle error sentinel (single-item list with 'error' key)
    if results and len(results) == 1 and "error" in results[0]:
        click.echo(results[0].get("error", "No results found."), err=False)
        return

    if not results:
        click.echo("No results found.", err=False)
        return

    if json_output:
        import json

        click.echo(json.dumps({"results": list(results)}, indent=2))
    else:
        from rich.console import Console
        from rich.table import Table

        from ztlctl.services.docs import DocResult

        doc_results: list[DocResult] = [r for r in results if "score" in r]  # type: ignore[misc]
        table = Table(show_header=True, header_style="bold")
        table.add_column("Title", style="cyan", no_wrap=True)
        table.add_column("Score", justify="right")
        table.add_column("Excerpt")
        for r in doc_results:
            table.add_row(r["title"], f"{r['score']:.2f}", r["excerpt"])
        Console().print(table)
