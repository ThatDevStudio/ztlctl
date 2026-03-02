#!/usr/bin/env python3
"""Build release assets and emit a manifest consumed by downstream jobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT / "pyproject.toml"
DEFAULT_OUTPUT = ROOT / "dist" / "release-manifest.json"


def clean_repository_url(url: str) -> str:
    """Normalize the configured repository URL."""
    return url.removesuffix(".git").rstrip("/")


def load_repository_url() -> str:
    """Read the repository URL from pyproject.toml."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project_urls = pyproject["project"]["urls"]
    repository = project_urls.get("Repository")
    if not isinstance(repository, str) or not repository:
        raise ValueError("pyproject.toml is missing project.urls.Repository")
    return clean_repository_url(repository)


def load_project_version() -> str:
    """Read the project version from pyproject.toml."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    version = pyproject["project"].get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml is missing project.version")
    return version


def normalize_tag(tag: str) -> str:
    """Normalize a release tag to the project's v-prefixed form."""
    cleaned = tag.strip()
    if not cleaned:
        raise ValueError("release tag must not be empty")
    return cleaned if cleaned.startswith("v") else f"v{cleaned}"


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run git in the repository root."""
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def verify_tag_exists(tag: str) -> None:
    """Ensure the requested tag exists locally."""
    result = run_git(["rev-parse", "--verify", tag])
    if result.returncode != 0:
        raise ValueError(f"Release tag {tag!r} does not exist locally")


def commit_sha_for_tag(tag: str) -> str:
    """Resolve the commit SHA for the annotated tag."""
    result = run_git(["rev-parse", f"{tag}^{{commit}}"])
    if result.returncode != 0:
        raise ValueError(f"Could not resolve commit for tag {tag!r}")
    return result.stdout.strip()


def build_tarball(*, tag: str, version: str, output_dir: Path) -> Path:
    """Build the release tarball for the given tag."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tarball_path = output_dir / f"ztlctl-{version}.tar.gz"
    result = subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix=ztlctl-{version}/",
            "-o",
            str(tarball_path),
            tag,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git archive failed for {tag}")
    return tarball_path


def sha256_digest(path: Path) -> str:
    """Return the sha256 digest for a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    """Render a stable path for manifest output."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_release_manifest(*, output_path: Path, release_tag: str | None = None) -> dict[str, str]:
    """Build the release tarball and manifest for a tag."""
    repository = load_repository_url()
    if release_tag is None:
        version = load_project_version()
        tag = f"v{version}"
    else:
        tag = normalize_tag(release_tag)
        version = tag.removeprefix("v")

    verify_tag_exists(tag)
    commit_sha = commit_sha_for_tag(tag)
    tarball_path = build_tarball(tag=tag, version=version, output_dir=output_path.parent)
    asset_name = tarball_path.name
    manifest = {
        "version": version,
        "tag": tag,
        "commit_sha": commit_sha,
        "asset_name": asset_name,
        "asset_path": display_path(tarball_path),
        "source_sha256": sha256_digest(tarball_path),
        "repository": repository,
        "release_url": f"{repository}/releases/tag/{tag}",
        "download_url": f"{repository}/releases/download/{tag}/{asset_name}",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-tag",
        help="Existing release tag to rebuild manifest from.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the generated release manifest.",
    )
    args = parser.parse_args()

    try:
        manifest = build_release_manifest(output_path=args.output, release_tag=args.release_tag)
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {display_path(args.output)} for {manifest['tag']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
