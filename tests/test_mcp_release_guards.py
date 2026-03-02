"""Regression guards for versionless MCP config assets."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_FILES = [
    ROOT / "plugin" / ".mcp.json",
    ROOT / "src" / "ztlctl" / "templates" / "agent_workflow" / "claude" / ".mcp.json.jinja",
]
FORBIDDEN_PATTERNS = (
    "ztlctl==",
    "/releases/download/",
    "sha256",
)


def test_mcp_configs_do_not_embed_release_metadata() -> None:
    for path in MCP_FILES:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in text, f"{path} unexpectedly contains {pattern!r}"
