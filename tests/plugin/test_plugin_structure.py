"""Automated validation of plugin layout, manifest fields, and stdout cleanliness."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Resolve project root from this file's location:
# tests/plugin/test_plugin_structure.py -> tests/plugin -> tests -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugin"


def test_plugin_directory_structure() -> None:
    """Plugin root has required directories; .claude-plugin/ contains only plugin.json."""
    # Required directories at plugin root level
    assert (PLUGIN_DIR / ".claude-plugin").is_dir(), "plugin/.claude-plugin/ missing"
    assert (PLUGIN_DIR / "skills").is_dir(), "plugin/skills/ missing"
    assert (PLUGIN_DIR / "agents").is_dir(), "plugin/agents/ missing"
    assert (PLUGIN_DIR / "hooks").is_dir(), "plugin/hooks/ missing"
    assert (PLUGIN_DIR / "commands").is_dir(), "plugin/commands/ missing"

    # .mcp.json at plugin root
    assert (PLUGIN_DIR / ".mcp.json").is_file(), "plugin/.mcp.json missing"

    # .claude-plugin/ must contain plugin.json
    assert (PLUGIN_DIR / ".claude-plugin" / "plugin.json").is_file(), (
        "plugin/.claude-plugin/plugin.json missing"
    )

    # .claude-plugin/ must NOT contain skills/, hooks/, agents/, commands/ inside it
    claude_plugin_dir = PLUGIN_DIR / ".claude-plugin"
    for forbidden in ("skills", "hooks", "agents", "commands"):
        assert not (claude_plugin_dir / forbidden).exists(), (
            f"plugin/.claude-plugin/{forbidden}/ must not exist — place it at plugin root"
        )


def test_plugin_json_required_fields() -> None:
    """plugin.json has all required fields."""
    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    required_fields = [
        "name",
        "version",
        "description",
        "author",
        "repository",
        "license",
        "commands",
        "hooks",
    ]
    for field in required_fields:
        assert field in data, f"plugin.json missing required field: {field!r}"


def test_plugin_json_name_kebab_case() -> None:
    """plugin.json name is lowercase kebab-case."""
    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = data["name"]
    assert re.fullmatch(r"[a-z][a-z0-9-]*", name), (
        f"plugin.json name {name!r} is not kebab-case (must match [a-z][a-z0-9-]*)"
    )


def test_mcp_json_has_pythonunbuffered() -> None:
    """plugin/.mcp.json has PYTHONUNBUFFERED=1 to prevent stdio transport buffering stalls."""
    mcp_path = PLUGIN_DIR / ".mcp.json"
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    env = data["mcpServers"]["ztlctl"]["env"]
    assert env.get("PYTHONUNBUFFERED") == "1", (
        f"plugin/.mcp.json mcpServers.ztlctl.env.PYTHONUNBUFFERED must be '1', got: {env!r}"
    )


def test_hook_scripts_executable() -> None:
    """All .sh files under plugin/hooks/scripts/ have execute permission."""
    scripts_dir = PLUGIN_DIR / "hooks" / "scripts"
    scripts = list(scripts_dir.glob("*.sh"))
    assert scripts, f"No .sh files found in {scripts_dir}"
    for script in scripts:
        assert os.access(script, os.X_OK), (
            f"{script} does not have execute permission — run: chmod +x {script}"
        )


def test_vault_gate_hook_registered() -> None:
    """hooks.json has PreToolUse entry with mcp__ztlctl__ matcher and vault-gate.sh command."""
    hooks_path = PLUGIN_DIR / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert "PreToolUse" in data["hooks"], "hooks.json missing 'PreToolUse' key"

    pre_tool_use_entries = data["hooks"]["PreToolUse"]
    found_matcher = False
    found_vault_gate = False
    for entry in pre_tool_use_entries:
        matcher = entry.get("matcher", "")
        if "mcp__ztlctl__" in matcher:
            found_matcher = True
        for hook in entry.get("hooks", []):
            command = hook.get("command", "")
            if "vault-gate.sh" in command:
                found_vault_gate = True

    assert found_matcher, "hooks.json PreToolUse entry missing matcher containing 'mcp__ztlctl__'"
    assert found_vault_gate, "hooks.json PreToolUse hook command missing 'vault-gate.sh'"


def test_vault_gate_blocks_without_vault(tmp_path: Path) -> None:
    """vault-gate.sh exits with code 2 and emits 'ztlctl init' hint when no vault exists."""
    vault_gate = PLUGIN_DIR / "hooks" / "scripts" / "vault-gate.sh"
    result = subprocess.run(
        ["bash", str(vault_gate)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, (
        f"vault-gate.sh should exit 2 without vault, got {result.returncode}. "
        f"stderr: {result.stderr!r}"
    )
    assert "ztlctl init" in result.stderr, (
        f"vault-gate.sh stderr should contain 'ztlctl init', got: {result.stderr!r}"
    )


def test_vault_gate_passes_with_vault(tmp_path: Path) -> None:
    """vault-gate.sh exits with code 0 when ztlctl.toml exists in the working directory."""
    vault_gate = PLUGIN_DIR / "hooks" / "scripts" / "vault-gate.sh"
    # Create a ztlctl.toml config in the temp dir to simulate an initialized vault
    (tmp_path / "ztlctl.toml").write_text('[vault]\nname = "test"\n', encoding="utf-8")

    result = subprocess.run(
        ["bash", str(vault_gate)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"vault-gate.sh should exit 0 with vault present, got {result.returncode}. "
        f"stderr: {result.stderr!r}"
    )


def test_no_paths_outside_plugin_root() -> None:
    """No file in plugin/ contains '../' path traversals (security requirement)."""
    violations: list[str] = []
    for path in PLUGIN_DIR.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # skip binary files
        if "../" in content:
            rel = path.relative_to(PROJECT_ROOT)
            violations.append(str(rel))

    assert not violations, (
        "Files containing '../' path traversals (not allowed in plugin files): "
        + textwrap.indent("\n".join(violations), "  ")
    )


def test_hook_paths_use_plugin_root_var() -> None:
    """All command fields in hooks.json use ${CLAUDE_PLUGIN_ROOT} for plugin-relative paths."""
    hooks_path = PLUGIN_DIR / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text(encoding="utf-8"))

    violations: list[str] = []
    for event, entries in data["hooks"].items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                # Only check commands that reference a script path
                if ".sh" in command or "/scripts/" in command or "/hooks/" in command:
                    if "${CLAUDE_PLUGIN_ROOT}" not in command:
                        violations.append(
                            f"{event} hook command missing ${{CLAUDE_PLUGIN_ROOT}}: {command!r}"
                        )

    assert not violations, (
        "Hook commands must use ${CLAUDE_PLUGIN_ROOT} for all plugin-relative paths:\n"
        + textwrap.indent("\n".join(violations), "  ")
    )


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("mcp") is None,
    reason="mcp extra not installed — run: uv run pip install ztlctl[mcp]",
)
def test_stdio_no_stdout_pollution(tmp_path: Path) -> None:
    """MCP stdio server produces only valid JSON on stdout (no banners or print output)."""
    # Create a minimal vault config
    config_path = tmp_path / "ztlctl.toml"
    config_path.write_text(
        '[vault]\nname = "plugin-test"\nclient = "none"\n\n[agent]\ntone = "minimal"\n',
        encoding="utf-8",
    )

    # JSON-RPC initialize request
    initialize_request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.0.1"},
            },
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ztlctl",
            "--sync",
            "-c",
            str(config_path),
            "serve",
            "--transport",
            "stdio",
        ],
        input=initialize_request,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )

    stdout = result.stdout
    assert stdout, (
        f"MCP server produced no stdout. returncode={result.returncode}, stderr={result.stderr!r}"
    )

    # Every non-empty line of stdout must be valid JSON
    non_json_lines: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            non_json_lines.append(repr(line))

    assert not non_json_lines, (
        "MCP stdio server emitted non-JSON bytes on stdout (corrupts JSON-RPC transport):\n"
        + textwrap.indent("\n".join(non_json_lines), "  ")
        + f"\nFull stdout: {stdout!r}"
    )
