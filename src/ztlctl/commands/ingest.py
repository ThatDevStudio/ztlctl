"""Command group: text-first ingestion and source capture."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.ingest import IngestService

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext


_INGEST_EXAMPLES = """\
  ztlctl ingest text "OAuth notes" --stdin
  ztlctl ingest file ./notes/source.md --as reference
  ztlctl ingest url https://example.com/article --provider mock --as reference
  ztlctl ingest providers"""


def _common_target_options[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    func = click.option(
        "--no-reweave",
        "skip_reweave",
        is_flag=True,
        help="Skip post-create reweave for this ingest operation.",
    )(func)
    func = click.option("--dry-run", is_flag=True, help="Preview the normalized ingest payload.")(
        func
    )
    func = click.option("--summary", default=None, help="Optional summary or framing text.")(func)
    func = click.option("--subtype", default=None, help="Optional target subtype.")(func)
    func = click.option("--session", default=None, help="Session ID (LOG-NNNN).")(func)
    func = click.option("--tags", multiple=True, help="Tags (repeatable).")(func)
    func = click.option("--topic", default=None, help="Topic subdirectory.")(func)
    func = click.option(
        "--as",
        "target_type",
        type=click.Choice(["reference", "note"]),
        default=None,
        help="Target durable artifact type.",
    )(func)
    return func


@click.group(cls=ZtlGroup, examples=_INGEST_EXAMPLES)
@click.pass_obj
def ingest(app: AppContext) -> None:
    """Ingest text and source material into the vault."""


@ingest.command(
    examples="""\
  ztlctl ingest text "OAuth notes" --stdin
  ztlctl ingest text "Meeting notes" --body-file ./notes.txt --as note"""
)
@click.argument("title")
@click.option("--stdin", "from_stdin", is_flag=True, help="Read content from stdin.")
@click.option("--body-file", type=click.Path(exists=True, dir_okay=False), default=None)
@_common_target_options
@click.pass_obj
def text(
    app: AppContext,
    title: str,
    from_stdin: bool,
    body_file: str | None,
    target_type: str | None,
    topic: str | None,
    tags: tuple[str, ...],
    session: str | None,
    subtype: str | None,
    summary: str | None,
    dry_run: bool,
    skip_reweave: bool,
) -> None:
    """Ingest raw text into a note or reference."""
    if from_stdin:
        body = sys.stdin.read()
    elif body_file is not None:
        body = Path(body_file).read_text(encoding="utf-8")
    else:
        raise click.BadParameter("Provide either --stdin or --body-file")

    result = IngestService(app.vault).ingest_text(
        title,
        body,
        target_type=target_type,
        topic=topic,
        tags=list(tags) if tags else None,
        session=session,
        subtype=subtype,
        summary=summary,
        dry_run=dry_run,
        no_reweave=skip_reweave,
    )
    app.emit(result)


@ingest.command(
    examples="""\
  ztlctl ingest file ./source.md --as reference
  ztlctl ingest file ./notes.txt --title "Imported notes" --as note"""
)
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--title", default=None, help="Override title (defaults to filename stem).")
@_common_target_options
@click.pass_obj
def file(
    app: AppContext,
    path: str,
    title: str | None,
    target_type: str | None,
    topic: str | None,
    tags: tuple[str, ...],
    session: str | None,
    subtype: str | None,
    summary: str | None,
    dry_run: bool,
    skip_reweave: bool,
) -> None:
    """Ingest a plain text or markdown file."""
    result = IngestService(app.vault).ingest_file(
        Path(path),
        title=title,
        target_type=target_type,
        topic=topic,
        tags=list(tags) if tags else None,
        session=session,
        subtype=subtype,
        summary=summary,
        dry_run=dry_run,
        no_reweave=skip_reweave,
    )
    app.emit(result)


@ingest.command(
    examples="""\
  ztlctl ingest url https://example.com/article --provider mock --as reference
  ztlctl ingest url https://example.com/spec --summary "Key source for auth redesign" """
)
@click.argument("url")
@click.option("--provider", default=None, help="Explicit source provider name.")
@click.option("--title", default=None, help="Override title (defaults to provider/title hint).")
@_common_target_options
@click.pass_obj
def url(
    app: AppContext,
    url: str,
    provider: str | None,
    title: str | None,
    target_type: str | None,
    topic: str | None,
    tags: tuple[str, ...],
    session: str | None,
    subtype: str | None,
    summary: str | None,
    dry_run: bool,
    skip_reweave: bool,
) -> None:
    """Ingest a URL through a source provider."""
    result = IngestService(app.vault).ingest_url(
        url,
        provider=provider,
        title=title,
        target_type=target_type,
        topic=topic,
        tags=list(tags) if tags else None,
        session=session,
        subtype=subtype,
        summary=summary,
        dry_run=dry_run,
        no_reweave=skip_reweave,
    )
    app.emit(result)


@ingest.command(examples="ztlctl ingest providers")
@click.pass_obj
def providers(app: AppContext) -> None:
    """List registered source providers."""
    app.emit(IngestService(app.vault).list_providers())
