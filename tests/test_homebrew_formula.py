"""Tests for Homebrew formula generation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "update_homebrew_formula.py"
FORMULA = ROOT / "Formula" / "ztlctl.rb"

pytestmark = pytest.mark.skipif(shutil.which("brew") is None, reason="Homebrew is required")


def test_homebrew_formula_is_current(tmp_path: Path) -> None:
    output = tmp_path / "ztlctl.rb"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        check=True,
    )
    assert output.read_text(encoding="utf-8") == FORMULA.read_text(encoding="utf-8")
