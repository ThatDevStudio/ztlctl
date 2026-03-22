"""Automated validation of plugin layout, manifest fields, and stdout cleanliness."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

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


# ---------------------------------------------------------------------------
# Helpers for SKILL.md parsing
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "when",
        "use",
        "for",
        "to",
        "or",
        "and",
        "in",
        "is",
        "of",
        "with",
        "that",
        "on",
        "be",
        "as",
        "are",
        "by",
        "at",
        "from",
        "it",
        "its",
        "this",
        "any",
        "all",
        "if",
        "their",
        "your",
        "my",
        "not",
        "no",
        "do",
        "will",
        "can",
        "has",
        "have",
        "been",
        "was",
        "were",
        "but",
        "so",
        "up",
        "out",
        "into",
        "about",
        "before",
        "after",
        "than",
        "more",
        "such",
        "each",
        "they",
        "them",
        "then",
        "which",
        "who",
    }
)

_WRITE_TOOL_NAMES = frozenset(
    {
        "create_note",
        "create_reference",
        "create_task",
        "session_start",
        "session_close",
        "confirm_contradiction",
        "reweave",
    }
)

# Match tool names only when used as actual function call templates (tool_name(...)).
# This avoids false positives from prose mentions like "`create_note`" or
# "the session_close MCP tool" which are documentation references, not invocations.
# Pattern: tool_name followed by '(' (with optional whitespace) — indicates a call template.
_WRITE_TOOL_CALL_PATTERN = re.compile(
    r"(?:" + "|".join(re.escape(t) for t in sorted(_WRITE_TOOL_NAMES)) + r")\s*\("
)

_AGENT_ALLOWED_FIELDS = frozenset(
    {
        "name",
        "description",
        "model",
        "effort",
        "maxTurns",
        "tools",
        "disallowedTools",
        "skills",
        "memory",
        "background",
        "isolation",
    }
)


def _parse_skill_frontmatter(path: Path) -> dict[str, Any]:
    """Return frontmatter dict for a SKILL.md using ruamel.yaml."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(parts[1])
    return dict(data) if data else {}


def _parse_skill_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    """Return (frontmatter dict, body text) for a SKILL.md."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(parts[1])
    return dict(data) if data else {}, parts[2]


def _parse_agent_frontmatter(path: Path) -> dict[str, Any]:
    """Return frontmatter dict for an agent .md file using ruamel.yaml."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(parts[1])
    return dict(data) if data else {}


def _significant_words(text: str) -> set[str]:
    """Return lowercase alpha words from text, excluding stop words."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Return Jaccard coefficient between two sets."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


# ---------------------------------------------------------------------------
# Distribution checklist tests (Pitfall coverage)
# ---------------------------------------------------------------------------


def test_plugin_json_version_semver() -> None:
    """plugin.json version matches semver and is >= 1.0.0 (Pitfall #3)."""
    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = data.get("version", "")

    assert re.fullmatch(r"\d+\.\d+\.\d+", version), (
        f"plugin.json version {version!r} does not match semver (\\d+.\\d+.\\d+)"
    )

    major, minor, patch = (int(x) for x in version.split("."))
    assert (major, minor, patch) >= (1, 0, 0), f"plugin.json version {version!r} must be >= 1.0.0"


def test_plugin_changelog_exists() -> None:
    """plugin/CHANGELOG.md exists and contains the version from plugin.json (Pitfall #3)."""
    changelog_path = PLUGIN_DIR / "CHANGELOG.md"
    assert changelog_path.is_file(), (
        "plugin/CHANGELOG.md is missing — required by distribution checklist"
    )

    manifest_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = data.get("version", "")

    content = changelog_path.read_text(encoding="utf-8")
    assert version in content, (
        f"plugin/CHANGELOG.md does not contain the current plugin version {version!r}"
    )


@pytest.mark.parametrize(
    "skill_name",
    [d.name for d in (PLUGIN_DIR / "skills").iterdir() if d.is_dir()],
)
def test_skill_line_counts_under_limit(skill_name: str) -> None:
    """Each SKILL.md must be under 500 lines to avoid context window bloat (Pitfall #7)."""
    skill_path = PLUGIN_DIR / "skills" / skill_name / "SKILL.md"
    assert skill_path.is_file(), f"SKILL.md missing for skill: {skill_name}"
    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    assert line_count < 500, (
        f"plugin/skills/{skill_name}/SKILL.md has {line_count} lines — must be under 500"
    )


@pytest.mark.parametrize(
    "skill_name",
    [d.name for d in (PLUGIN_DIR / "skills").iterdir() if d.is_dir()],
)
def test_all_skills_have_name_field(skill_name: str) -> None:
    """Every SKILL.md must have a name: field in frontmatter."""
    skill_path = PLUGIN_DIR / "skills" / skill_name / "SKILL.md"
    assert skill_path.is_file(), f"SKILL.md missing for skill: {skill_name}"
    fm = _parse_skill_frontmatter(skill_path)
    assert "name" in fm, (
        f"plugin/skills/{skill_name}/SKILL.md frontmatter missing required 'name:' field"
    )
    assert fm["name"], f"plugin/skills/{skill_name}/SKILL.md frontmatter 'name:' field is empty"


def test_skill_descriptions_no_overlap() -> None:
    """No two skill descriptions share more than 50% of significant words (Pitfall #6)."""
    skills_dir = PLUGIN_DIR / "skills"
    skill_descriptions: dict[str, set[str]] = {}

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            continue
        fm = _parse_skill_frontmatter(skill_path)
        desc = fm.get("description", "")
        if isinstance(desc, str):
            skill_descriptions[skill_dir.name] = _significant_words(desc)

    overlapping_pairs: list[str] = []
    skill_names = sorted(skill_descriptions)
    for i, name_a in enumerate(skill_names):
        for name_b in skill_names[i + 1 :]:
            coeff = _jaccard(skill_descriptions[name_a], skill_descriptions[name_b])
            if coeff > 0.5:
                overlapping_pairs.append(f"  {name_a} <-> {name_b}: Jaccard={coeff:.2f}")

    assert not overlapping_pairs, (
        "Skill description pairs with >50% word overlap (activation confusion risk):\n"
        + "\n".join(overlapping_pairs)
    )


@pytest.mark.parametrize(
    "skill_name",
    [d.name for d in (PLUGIN_DIR / "skills").iterdir() if d.is_dir()],
)
def test_side_effect_skills_have_disable_model_invocation(skill_name: str) -> None:
    """Skills with write-op tool calls must have disable-model-invocation: true (Pitfall #20)."""
    skill_path = PLUGIN_DIR / "skills" / skill_name / "SKILL.md"
    assert skill_path.is_file(), f"SKILL.md missing for skill: {skill_name}"
    fm, body = _parse_skill_frontmatter_and_body(skill_path)

    # Detect write-tool calls via function-call syntax (tool_name( or `tool_name`)
    # Prose mentions of tool names (e.g., "the reweave system") are not flagged.
    found_tools = sorted(
        {m.group(0).strip("`").rstrip("(").strip() for m in _WRITE_TOOL_CALL_PATTERN.finditer(body)}
    )
    if not found_tools:
        return  # read-only skill — no requirement

    disable_flag = fm.get("disable-model-invocation", False)
    assert disable_flag is True, (
        f"plugin/skills/{skill_name}/SKILL.md references write-operation MCP tools "
        f"({found_tools}) "
        f"but lacks 'disable-model-invocation: true' in frontmatter (Pitfall #20)"
    )


@pytest.mark.parametrize(
    "agent_name",
    [p.stem for p in (PLUGIN_DIR / "agents").glob("*.md")],
)
def test_agent_frontmatter_no_unsupported_fields(agent_name: str) -> None:
    """Plugin agents must not use unsupported frontmatter fields (Pitfall #19)."""
    agent_path = PLUGIN_DIR / "agents" / f"{agent_name}.md"
    fm = _parse_agent_frontmatter(agent_path)

    unsupported = {"hooks", "mcpServers", "permissionMode"}
    violations = sorted(set(fm.keys()) & unsupported)
    assert not violations, (
        f"plugin/agents/{agent_name}.md uses unsupported frontmatter fields: "
        f"{violations!r}. Plugin agents only support: {sorted(_AGENT_ALLOWED_FIELDS)!r}"
    )


def test_mcp_json_no_path_traversals() -> None:
    """plugin/.mcp.json does not contain '../' path traversals (Pitfall #12)."""
    mcp_path = PLUGIN_DIR / ".mcp.json"
    content = mcp_path.read_text(encoding="utf-8")
    assert "../" not in content, (
        "plugin/.mcp.json contains '../' path traversal — all paths must be self-contained"
    )


def test_readme_component_counts_accurate() -> None:
    """README.md component counts match actual directory contents (Skills, Commands, Agents)."""
    readme_path = PLUGIN_DIR / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    actual_skills = sum(1 for d in (PLUGIN_DIR / "skills").iterdir() if d.is_dir())
    actual_commands = sum(1 for f in (PLUGIN_DIR / "commands").glob("*.md"))
    actual_agents = sum(1 for f in (PLUGIN_DIR / "agents").glob("*.md"))

    # Find the component count table — look for | Skills | N | pattern
    skills_match = re.search(r"\|\s*Skills\s*\|\s*(\d+)\s*\|", content)
    commands_match = re.search(r"\|\s*Commands\s*\|\s*(\d+)\s*\|", content)
    agents_match = re.search(r"\|\s*Agents\s*\|\s*(\d+)\s*\|", content)

    assert skills_match, "README.md missing 'Skills' row in component count table"
    assert commands_match, "README.md missing 'Commands' row in component count table"
    assert agents_match, "README.md missing 'Agents' row in component count table"

    readme_skills = int(skills_match.group(1))
    readme_commands = int(commands_match.group(1))
    readme_agents = int(agents_match.group(1))

    assert readme_skills == actual_skills, (
        f"README.md says {readme_skills} skills but plugin/skills/ has {actual_skills} directories"
    )
    assert readme_commands == actual_commands, (
        f"README.md says {readme_commands} commands but plugin/commands/ has "
        f"{actual_commands} .md files"
    )
    assert readme_agents == actual_agents, (
        f"README.md says {readme_agents} agents but plugin/agents/ has {actual_agents} .md files"
    )


def test_hook_exit_codes_documented() -> None:
    """vault-gate.sh uses both exit 0 (pass) and exit 2 (block) — correct codes (Pitfall #9)."""
    vault_gate = PLUGIN_DIR / "hooks" / "scripts" / "vault-gate.sh"
    assert vault_gate.is_file(), f"vault-gate.sh missing at {vault_gate}"
    content = vault_gate.read_text(encoding="utf-8")
    assert "exit 0" in content, (
        "vault-gate.sh missing 'exit 0' — should exit 0 when vault is present (allow)"
    )
    assert "exit 2" in content, (
        "vault-gate.sh missing 'exit 2' — should exit 2 when vault is absent (block)"
    )
