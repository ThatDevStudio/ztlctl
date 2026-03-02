"""Tests for Homebrew formula generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "update_homebrew_formula.py"


def write_manifest(tmp_path: Path, *, version: str = "9.9.9") -> Path:
    """Write a release manifest fixture."""
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": version,
                "tag": f"v{version}",
                "commit_sha": "abc123",
                "asset_name": f"ztlctl-{version}.tar.gz",
                "asset_path": f"dist/ztlctl-{version}.tar.gz",
                "source_sha256": "0" * 64,
                "repository": "https://github.com/example/ztlctl",
                "release_url": f"https://github.com/example/ztlctl/releases/tag/v{version}",
                "download_url": (
                    f"https://github.com/example/ztlctl/releases/download/v{version}/"
                    f"ztlctl-{version}.tar.gz"
                ),
            }
        ),
        encoding="utf-8",
    )
    return manifest


def test_homebrew_formula_uses_manifest_release_metadata(tmp_path: Path) -> None:
    output = tmp_path / "ztlctl.rb"
    manifest = write_manifest(tmp_path)

    subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--output", str(output)],
        cwd=ROOT,
        check=True,
    )

    text = output.read_text(encoding="utf-8")
    assert (
        'url "https://github.com/example/ztlctl/releases/download/v9.9.9/ztlctl-9.9.9.tar.gz"'
        in text
    )
    assert 'sha256 "' + ("0" * 64) + '"' in text


def test_homebrew_formula_requires_manifest_fields(tmp_path: Path) -> None:
    output = tmp_path / "ztlctl.rb"
    manifest = tmp_path / "release-manifest.json"
    manifest.write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--output", str(output)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "missing required fields" in result.stderr


def test_homebrew_formula_does_not_require_existing_git_tag(tmp_path: Path) -> None:
    output = tmp_path / "ztlctl.rb"
    manifest = write_manifest(tmp_path, version="99.99.99")

    subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--output", str(output)],
        cwd=ROOT,
        check=True,
    )

    text = output.read_text(encoding="utf-8")
    assert "99.99.99" in text


def test_homebrew_formula_output_is_deterministic(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path, version="1.2.3")
    first_output = tmp_path / "first.rb"
    second_output = tmp_path / "second.rb"

    subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--output", str(first_output)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest), "--output", str(second_output)],
        cwd=ROOT,
        check=True,
    )

    assert first_output.read_text(encoding="utf-8") == second_output.read_text(encoding="utf-8")
