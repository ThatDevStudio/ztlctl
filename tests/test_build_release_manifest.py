"""Tests for release manifest generation."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_release_manifest.py"


def load_script_module(module_name: str):
    """Load a script module from disk for direct unit testing."""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def init_repo(tmp_path: Path) -> Path:
    """Create a small tagged git repository for manifest tests."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            "\n"
            "[project.urls]\n"
            'Repository = "https://github.com/example/demo"\n'
        ),
        encoding="utf-8",
    )
    (repo / "README.md").write_text("demo\n", encoding="utf-8")
    (repo / "demo.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    subprocess.run(["git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"], cwd=repo, check=True)
    return repo


def test_build_release_manifest_normal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_script_module("build_release_manifest_normal")
    repo = init_repo(tmp_path)
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PYPROJECT_PATH", repo / "pyproject.toml")

    output = repo / "dist" / "release-manifest.json"
    manifest = module.build_release_manifest(output_path=output)

    assert manifest["version"] == "0.1.0"
    assert manifest["tag"] == "v0.1.0"
    assert manifest["asset_name"] == "ztlctl-0.1.0.tar.gz"
    assert manifest["asset_path"] == "dist/ztlctl-0.1.0.tar.gz"
    assert manifest["download_url"].endswith("/releases/download/v0.1.0/ztlctl-0.1.0.tar.gz")
    assert manifest["release_url"].endswith("/releases/tag/v0.1.0")
    assert len(manifest["source_sha256"]) == 64
    assert output.exists()
    assert (repo / manifest["asset_path"]).exists()


def test_build_release_manifest_recovery_uses_explicit_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_script_module("build_release_manifest_recovery")
    repo = init_repo(tmp_path)
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PYPROJECT_PATH", repo / "pyproject.toml")
    (repo / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "demo"\n'
            'version = "9.9.9"\n'
            "\n"
            "[project.urls]\n"
            'Repository = "https://github.com/example/demo"\n'
        ),
        encoding="utf-8",
    )

    manifest = module.build_release_manifest(
        output_path=repo / "dist" / "release-manifest.json",
        release_tag="v0.1.0",
    )

    assert manifest["version"] == "0.1.0"
    assert manifest["tag"] == "v0.1.0"


def test_build_release_manifest_sha_is_deterministic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_script_module("build_release_manifest_deterministic")
    repo = init_repo(tmp_path)
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PYPROJECT_PATH", repo / "pyproject.toml")

    first = module.build_release_manifest(
        output_path=repo / "dist" / "release-manifest.json",
        release_tag="v0.1.0",
    )
    second = module.build_release_manifest(
        output_path=repo / "dist" / "release-manifest.json",
        release_tag="v0.1.0",
    )

    assert first["source_sha256"] == second["source_sha256"]
