"""Generate docs/llms-full.txt by concatenating all docs pages in nav order.

Keep NAV_ORDER in sync with the nav: section in mkdocs.yml.
Run: python scripts/gen_llms_full_txt.py
"""

from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
OUTPUT = DOCS_DIR / "llms-full.txt"

# Nav order matching mkdocs.yml nav: section exactly.
# IMPORTANT: Keep this in sync with mkdocs.yml nav: when nav changes.
NAV_ORDER = [
    (
        "Getting Started",
        ["index.md", "installation.md", "quickstart.md"],
    ),
    (
        "User Guide",
        [
            "guide/index.md",
            "tutorial.md",
            "concepts.md",
            "paradigms.md",
            "obsidian.md",
            "plugins.md",
            "agentic-workflows.md",
            "commands.md",
            "configuration.md",
            "troubleshooting.md",
            "best-practices.md",
        ],
    ),
    (
        "Developer Guide",
        [
            "dev/index.md",
            "development.md",
            "plugin-guide.md",
            "api-reference.md",
            "mcp.md",
            "agents.md",
        ],
    ),
]


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter block if present (--- ... --- at file start)."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip("\n")
    return text


def main() -> None:
    parts: list[str] = []
    for section_name, files in NAV_ORDER:
        parts.append(f"# {section_name}\n\n")
        for filename in files:
            filepath = DOCS_DIR / filename
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                parts.append(strip_frontmatter(content))
                parts.append("\n\n---\n\n")
            else:
                print(f"WARNING: {filepath} not found — skipping")
    OUTPUT.write_text("".join(parts), encoding="utf-8")
    print(f"Written: {OUTPUT}")


if __name__ == "__main__":
    main()
