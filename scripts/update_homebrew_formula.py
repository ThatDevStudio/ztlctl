#!/usr/bin/env python3
"""Generate the Homebrew formula for ztlctl."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT / "pyproject.toml"
LOCK_PATH = ROOT / "uv.lock"
DEFAULT_OUTPUT = ROOT / "dist" / "ztlctl.rb"


def normalize_name(name: str) -> str:
    """Normalize a Python package name to PEP 503 form."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement_name(requirement: str) -> str:
    """Extract the package name from a PEP 508 requirement string."""
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        raise ValueError(f"Could not parse requirement name from {requirement!r}")
    return match.group(1)


def wheel_filename(url: str) -> str:
    """Return the wheel filename from a wheel URL."""
    return Path(urlparse(url).path).name


def parse_macos_version(filename: str) -> tuple[int, ...]:
    """Extract the macOS deployment target from a wheel filename."""
    match = re.search(r"macosx_(\d+)_(\d+)", filename)
    if match is None:
        return (999, 999)
    return int(match.group(1)), int(match.group(2))


class MarkerEvaluator:
    """Minimal evaluator for the subset of PEP 508 markers used in uv.lock."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = env

    def evaluate(self, expression: str) -> bool:
        tree = ast.parse(expression, mode="eval")
        return self._eval(tree.body)

    def _eval(self, node: ast.AST) -> bool | str:
        if isinstance(node, ast.BoolOp):
            values = [self._coerce_bool(self._eval(value)) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError(f"Unsupported boolean operator: {ast.dump(node)}")
        if isinstance(node, ast.Compare):
            left = self._coerce_str(self._eval(node.left))
            result = True
            for operator, comparator in zip(node.ops, node.comparators, strict=True):
                right = self._coerce_str(self._eval(comparator))
                if isinstance(operator, ast.Eq):
                    current = left == right
                elif isinstance(operator, ast.NotEq):
                    current = left != right
                elif isinstance(operator, ast.In):
                    current = left in right
                elif isinstance(operator, ast.NotIn):
                    current = left not in right
                else:
                    raise ValueError(f"Unsupported comparison operator: {ast.dump(operator)}")
                result = result and current
                left = right
            return result
        if isinstance(node, ast.Name):
            if node.id not in self.env:
                raise ValueError(f"Unsupported marker variable: {node.id}")
            return self.env[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        raise ValueError(f"Unsupported marker expression: {ast.dump(node)}")

    @staticmethod
    def _coerce_bool(value: bool | str) -> bool:
        if isinstance(value, bool):
            return value
        raise ValueError(f"Expected marker boolean, got string {value!r}")

    @staticmethod
    def _coerce_str(value: bool | str) -> str:
        if isinstance(value, str):
            return value
        raise ValueError(f"Expected marker string, got boolean {value!r}")


@dataclass(frozen=True)
class Artifact:
    """A fetchable source or wheel artifact for Homebrew."""

    url: str
    sha256: str


@dataclass(frozen=True)
class ReleaseMetadata:
    """Release metadata embedded into the generated formula."""

    version: str
    download_url: str
    source_sha256: str


def package_maps(lock_data: dict[str, object]) -> dict[str, dict[str, object]]:
    """Index uv.lock packages by normalized package name."""
    packages = lock_data.get("package")
    if not isinstance(packages, list):
        raise ValueError("uv.lock is missing package entries")
    result: dict[str, dict[str, object]] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        name = package.get("name")
        if isinstance(name, str):
            result[normalize_name(name)] = package
    return result


def marker_applies(dependency: dict[str, object], env: dict[str, str]) -> bool:
    """Return whether a dependency applies under the given marker environment."""
    marker = dependency.get("marker")
    if not isinstance(marker, str):
        return True
    return MarkerEvaluator(env).evaluate(marker)


def dependency_names(package: dict[str, object], env: dict[str, str]) -> list[str]:
    """Return normalized dependency names that apply in the current environment."""
    dependencies = package.get("dependencies", [])
    if not isinstance(dependencies, list):
        return []
    result: list[str] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        name = dependency.get("name")
        if isinstance(name, str) and marker_applies(dependency, env):
            result.append(normalize_name(name))
    return result


def dependency_closure(
    *,
    roots: Iterable[str],
    packages: dict[str, dict[str, object]],
    env: dict[str, str],
) -> set[str]:
    """Compute the runtime dependency closure for a given environment."""
    pending = list(roots)
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        package = packages.get(current)
        if package is None:
            raise ValueError(f"Package {current!r} is not present in uv.lock")
        pending.extend(dependency_names(package, env))
    return seen


def choose_common_wheel(package: dict[str, object]) -> Artifact | None:
    """Choose a wheel usable across architectures when one exists."""
    wheels = package.get("wheels", [])
    if not isinstance(wheels, list):
        return None
    best_any: Artifact | None = None
    best_universal: Artifact | None = None
    for wheel in wheels:
        if not isinstance(wheel, dict):
            continue
        url = wheel.get("url")
        sha256 = wheel.get("hash")
        if not isinstance(url, str) or not isinstance(sha256, str):
            continue
        filename = wheel_filename(url)
        if filename.endswith(".whl") and "none-any.whl" in filename:
            best_any = Artifact(url=url, sha256=sha256.removeprefix("sha256:"))
            break
        if filename.endswith(".whl") and "macosx" in filename and "universal2" in filename:
            if "cp313t" in filename:
                continue
            candidate = Artifact(url=url, sha256=sha256.removeprefix("sha256:"))
            if best_universal is None or parse_macos_version(filename) < parse_macos_version(
                wheel_filename(best_universal.url)
            ):
                best_universal = candidate
    return best_any or best_universal


def choose_arch_wheel(package: dict[str, object], arch: str) -> Artifact | None:
    """Choose a macOS cp313 wheel for the requested architecture."""
    wheels = package.get("wheels", [])
    if not isinstance(wheels, list):
        return None
    best: tuple[tuple[int, ...], Artifact] | None = None
    for wheel in wheels:
        if not isinstance(wheel, dict):
            continue
        url = wheel.get("url")
        sha256 = wheel.get("hash")
        if not isinstance(url, str) or not isinstance(sha256, str):
            continue
        filename = wheel_filename(url)
        if not filename.endswith(".whl"):
            continue
        if "macosx" not in filename or "cp313" not in filename or "cp313t" in filename:
            continue
        if arch == "arm" and "arm64" not in filename and "universal2" not in filename:
            continue
        if arch == "intel" and "x86_64" not in filename and "universal2" not in filename:
            continue
        version = parse_macos_version(filename)
        candidate = Artifact(url=url, sha256=sha256.removeprefix("sha256:"))
        if best is None or version < best[0]:
            best = (version, candidate)
    return None if best is None else best[1]


def choose_sdist(package: dict[str, object]) -> Artifact:
    """Return the source distribution artifact for a package."""
    sdist = package.get("sdist")
    if not isinstance(sdist, dict):
        raise ValueError(f"Package {package.get('name', '<unknown>')} is missing an sdist artifact")
    url = sdist.get("url")
    sha256 = sdist.get("hash")
    if not isinstance(url, str) or not isinstance(sha256, str):
        raise ValueError(
            f"Package {package.get('name', '<unknown>')} has incomplete sdist metadata"
        )
    return Artifact(url=url, sha256=sha256.removeprefix("sha256:"))


def choose_artifact(package: dict[str, object], arch: str) -> Artifact:
    """Choose the best Homebrew-installable artifact for an environment."""
    common = choose_common_wheel(package)
    if common is not None:
        return common
    arch_wheel = choose_arch_wheel(package, arch)
    if arch_wheel is not None:
        return arch_wheel
    return choose_sdist(package)


def render_resource(name: str, artifact: Artifact, indent: str = "  ") -> str:
    """Render a Homebrew resource block."""
    return (
        f'{indent}resource "{name}" do\n'
        f'{indent}  url "{artifact.url}"\n'
        f'{indent}  sha256 "{artifact.sha256}"\n'
        f"{indent}end\n"
    )


def format_runtime_resources(
    *,
    package_names: Iterable[str],
    packages: dict[str, dict[str, object]],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """Partition runtime resources into common, arm-only, and intel-only blocks."""
    common_blocks: list[tuple[str, str]] = []
    arm_blocks: list[tuple[str, str]] = []
    intel_blocks: list[tuple[str, str]] = []
    for package_name in sorted(package_names):
        package = packages[package_name]
        display_name = str(package["name"])
        arm_artifact = choose_artifact(package, "arm")
        intel_artifact = choose_artifact(package, "intel")
        if arm_artifact == intel_artifact:
            common_blocks.append((display_name, render_resource(display_name, arm_artifact)))
            continue
        arm_blocks.append(
            (display_name, render_resource(display_name, arm_artifact, indent="    "))
        )
        intel_blocks.append(
            (display_name, render_resource(display_name, intel_artifact, indent="    "))
        )
    return common_blocks, arm_blocks, intel_blocks


def load_release_metadata(
    *,
    manifest_path: Path | None,
    version: str | None,
    source_sha256: str | None,
    download_url: str | None,
) -> ReleaseMetadata:
    """Load release metadata from a manifest or explicit CLI values."""
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        required_fields = {"version", "download_url", "source_sha256"}
        missing = sorted(field for field in required_fields if field not in manifest)
        if missing:
            missing_fields = ", ".join(missing)
            raise ValueError(f"{manifest_path} is missing required fields: {missing_fields}")
        manifest_version = manifest["version"]
        manifest_download_url = manifest["download_url"]
        manifest_sha256 = manifest["source_sha256"]
        if not isinstance(manifest_version, str) or not manifest_version:
            raise ValueError(f"{manifest_path} has an invalid version field")
        if not isinstance(manifest_download_url, str) or not manifest_download_url:
            raise ValueError(f"{manifest_path} has an invalid download_url field")
        if not isinstance(manifest_sha256, str) or not manifest_sha256:
            raise ValueError(f"{manifest_path} has an invalid source_sha256 field")
        return ReleaseMetadata(
            version=manifest_version,
            download_url=manifest_download_url,
            source_sha256=manifest_sha256,
        )

    if version is None or source_sha256 is None or download_url is None:
        raise ValueError(
            "Provide --manifest or all of --version, --source-sha256, and --download-url"
        )
    return ReleaseMetadata(
        version=version,
        download_url=download_url,
        source_sha256=source_sha256,
    )


def base_formula(
    *,
    release: ReleaseMetadata,
    description: str,
    homepage: str,
    repository: str,
    license_name: str,
    build_backend_names: list[str],
    common_resources: list[str],
    arm_resources: list[str],
    intel_resources: list[str],
) -> str:
    """Render the final formula body."""
    formula_description = description.replace("—", "-")
    resource_sections: list[str] = []
    if arm_resources:
        resource_sections.append("  on_arm do")
        resource_sections.extend(block.rstrip() for block in arm_resources)
        resource_sections.append("  end")
        resource_sections.append("")
    if intel_resources:
        resource_sections.append("  on_intel do")
        resource_sections.extend(block.rstrip() for block in intel_resources)
        resource_sections.append("  end")
        resource_sections.append("")
    resource_sections.extend(block.rstrip() for block in common_resources)
    resource_sections.append("")

    lines = [
        "# This file is autogenerated by scripts/update_homebrew_formula.py.",
        "class Ztlctl < Formula",
        "  include Language::Python::Virtualenv",
        "",
        f'  desc "{formula_description}"',
        f'  homepage "{homepage}"',
        f'  url "{release.download_url}"',
        f'  sha256 "{release.source_sha256}"',
        f'  license "{license_name}"',
        f'  head "{repository}.git", branch: "develop"',
        "",
        '  depends_on "libyaml"',
        '  depends_on "python@3.13"',
        "",
    ]
    lines.extend(resource_sections)
    build_backend_literal = " ".join(build_backend_names)
    lines.extend(
        [
            "  def install",
            '    venv = virtualenv_create(libexec, "python3.13")',
            f"    build_backend_names = %w[{build_backend_literal}]",
            (
                "    build_backend, runtime_resources = "
                "resources.partition { |resource| build_backend_names.include?(resource.name) }"
            ),
            "    venv.pip_install runtime_resources",
            "    venv.pip_install build_backend, build_isolation: false",
            "    venv.pip_install_and_link buildpath, build_isolation: false",
            "  end",
            "",
            "  test do",
            '    assert_match version.to_s, shell_output("#{bin}/ztlctl --version")',
            (
                '    system bin/"ztlctl", "--no-interact", "init", '
                'testpath/"vault", "--name", "brew-test", "--no-workflow"'
            ),
            '    assert_path_exists testpath/"vault"/"ztlctl.toml"',
            '    assert_path_exists testpath/"vault"/".ztlctl"/"ztlctl.db"',
            "  end",
            "end",
            "",
        ]
    )
    return "\n".join(lines)


def generate_formula(release: ReleaseMetadata) -> str:
    """Generate the Homebrew formula content from local project files."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    lock_data = tomllib.loads(LOCK_PATH.read_text(encoding="utf-8"))
    project = pyproject["project"]
    build_system = pyproject["build-system"]
    packages = package_maps(lock_data)
    direct_dependencies = {
        normalize_name(parse_requirement_name(requirement))
        for requirement in project["dependencies"]
    }
    build_dependencies = {
        normalize_name(parse_requirement_name(requirement))
        for requirement in build_system["requires"]
    }
    arm_env = {
        "sys_platform": "darwin",
        "platform_machine": "arm64",
        "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
        "extra": "",
    }
    intel_env = {
        "sys_platform": "darwin",
        "platform_machine": "x86_64",
        "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
        "extra": "",
    }
    runtime_names = dependency_closure(
        roots=direct_dependencies,
        packages=packages,
        env=arm_env,
    ) | dependency_closure(
        roots=direct_dependencies,
        packages=packages,
        env=intel_env,
    )
    build_backend_names = dependency_closure(
        roots=build_dependencies,
        packages=packages,
        env=arm_env,
    ) | dependency_closure(
        roots=build_dependencies,
        packages=packages,
        env=intel_env,
    )
    all_resource_names = runtime_names | build_backend_names

    homepage = str(project["urls"]["Homepage"])
    repository = str(project["urls"]["Repository"])
    common_runtime, arm_runtime, intel_runtime = format_runtime_resources(
        package_names=all_resource_names,
        packages=packages,
    )
    build_backend_display_names = sorted(
        str(packages[name]["name"]) for name in build_backend_names
    )
    common_resources = [block for _, block in sorted(common_runtime)]
    arm_resources = [block for _, block in sorted(arm_runtime)]
    intel_resources = [block for _, block in sorted(intel_runtime)]

    return base_formula(
        release=release,
        description=str(project["description"]),
        homepage=homepage,
        repository=repository,
        license_name=str(project["license"]),
        build_backend_names=build_backend_display_names,
        common_resources=common_resources,
        arm_resources=arm_resources,
        intel_resources=intel_resources,
    )


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to a release-manifest.json file.",
    )
    parser.add_argument(
        "--version",
        help="Release version to embed when no manifest is provided.",
    )
    parser.add_argument(
        "--source-sha256",
        help="Release tarball sha256 to embed when no manifest is provided.",
    )
    parser.add_argument(
        "--download-url",
        help="Release download URL to embed when no manifest is provided.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the generated formula file.",
    )
    args = parser.parse_args()

    try:
        release = load_release_metadata(
            manifest_path=args.manifest,
            version=args.version,
            source_sha256=args.source_sha256,
            download_url=args.download_url,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    formula = generate_formula(release)
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(formula, encoding="utf-8")
    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Wrote {display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
