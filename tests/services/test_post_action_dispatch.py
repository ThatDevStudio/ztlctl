"""Verify all write services call _dispatch_post_action_event.

Structural test: scans service ASTs to ensure every public method that
performs a vault.transaction() write also calls _dispatch_post_action_event.
This prevents future omissions from slipping through undetected.
"""

import ast
from pathlib import Path

SERVICE_DIR = Path("src/ztlctl/services")

# Methods that are known write operations but legitimately skip post_action:
# - _create_content_in_txn: private helper called by _create_content (which dispatches)
# - _apply_undo: private helper called by undo (which dispatches)
# - _prune_links: private helper called by prune (which dispatches)
# - _backup_db: helper, not a user-facing action
# - _fix_*: private helpers called by fix (which dispatches)
# - check: read operation, not a write — D-10 compliance
# - _connect: private helper called by reweave (which dispatches)
# - _cross_session_reweave: private helper called by close (which dispatches)
# - _orphan_sweep: private helper called by close (which dispatches)
# - _integrity_check: private helper called by close (which dispatches)
# - _check_*: read-only check helpers
# - materialize_metrics: uses engine.begin() not transaction(), graph metric update
# - log_entry: session utility, not a primary action (no controller post_action)
# - rollback: restore operation (no transaction() call, uses shutil.copy2)
EXEMPT_METHODS = {
    "_create_content_in_txn",
    "_apply_undo",
    "_prune_links",
    "_backup_db",
    "_fix_orphan_db_rows",
    "_fix_dangling_edges",
    "_fix_missing_fts",
    "_fix_resync_from_files",
    "_fix_reindex_edges",
    "_fix_reorder_frontmatter",
    "_connect",
    "_cross_session_reweave",
    "_orphan_sweep",
    "_integrity_check",
    "check",
    "_check_structural_validation",
    "_check_referential_integrity",
    "_check_schema_integrity",
    "_check_db_file_consistency",
    "_check_graph_health",
    "_check_garden_health",
    "_check_schema_version",
    "materialize_metrics",
    "log_entry",
    "rollback",
    "_remove_link_from_file",
    "_undo_add",
    "_undo_remove",
    "_prune_backups",
}


def test_write_services_dispatch_post_action() -> None:
    """Every public write method in services must call _dispatch_post_action_event."""
    service_files = [
        "create.py",
        "update.py",
        "session.py",
        "reweave.py",
        "check.py",
        "graph.py",
    ]
    missing = []
    for filename in service_files:
        path = SERVICE_DIR / filename
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name in EXEMPT_METHODS:
                    continue
                # Check if method has transaction() call (indicating a write)
                has_transaction = any(
                    isinstance(call, ast.Attribute) and call.attr == "transaction"
                    for call in ast.walk(item)
                    if isinstance(call, ast.Attribute)
                )
                if not has_transaction:
                    continue
                # Check if method calls _dispatch_post_action_event
                has_dispatch = any(
                    isinstance(call, ast.Attribute)
                    and call.attr == "_dispatch_post_action_event"
                    for call in ast.walk(item)
                    if isinstance(call, ast.Attribute)
                )
                if not has_dispatch:
                    missing.append(f"{filename}::{node.name}.{item.name}")

    assert not missing, (
        f"Write methods missing _dispatch_post_action_event: {missing}"
    )
