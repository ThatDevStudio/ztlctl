"""Tests for structlog configuration."""

from __future__ import annotations

import json
import logging
from collections.abc import Generator

import pytest
import structlog

from ztlctl.config.logging import configure_logging


@pytest.fixture(autouse=True)
def _restore_logging() -> Generator[None]:
    """Restore root logger state after each test."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    ztl = logging.getLogger("ztlctl")
    ztl_level = ztl.level
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)
    ztl.setLevel(ztl_level)


class TestConfigureLogging:
    def test_verbose_enables_debug(self) -> None:
        configure_logging(verbose=True, log_json=False)
        assert logging.getLogger("ztlctl").level == logging.DEBUG
        assert logging.getLogger().level == logging.WARNING

    def test_non_verbose_sets_warning(self) -> None:
        configure_logging(verbose=False, log_json=False)
        assert logging.getLogger("ztlctl").level == logging.WARNING

    def test_human_mode_output(self) -> None:
        configure_logging(verbose=True, log_json=False)
        log = structlog.get_logger("ztlctl.test")
        log.warning("hello world", key="val")
        # Smoke test — verify no exception; format depends on terminal

    def test_json_mode_output(self, capfd: pytest.CaptureFixture[str]) -> None:
        configure_logging(verbose=True, log_json=True)
        log = structlog.get_logger("ztlctl.test")
        log.warning("json test", answer=42)
        captured = capfd.readouterr()
        parsed = json.loads(captured.err.strip())
        assert parsed["event"] == "json test"
        assert parsed["answer"] == 42
        assert parsed["level"] == "warning"
        assert parsed["logger"] == "ztlctl.test"
        assert "timestamp" in parsed

    def test_stdlib_ztl_logger_gets_structured_fields(
        self, capfd: pytest.CaptureFixture[str]
    ) -> None:
        configure_logging(verbose=True, log_json=True)

        logging.getLogger("ztlctl.plugins.manager").debug("Registered plugin: probe")

        captured = capfd.readouterr()
        parsed = json.loads(captured.err.strip())
        assert parsed["event"] == "Registered plugin: probe"
        assert parsed["level"] == "debug"
        assert parsed["logger"] == "ztlctl.plugins.manager"
        assert "timestamp" in parsed

    def test_third_party_debug_is_suppressed(self, capfd: pytest.CaptureFixture[str]) -> None:
        configure_logging(verbose=True, log_json=True)

        logging.getLogger("alembic").debug("migration noise")
        logging.getLogger("copier").debug("template noise")

        captured = capfd.readouterr()
        assert captured.err == ""

    def test_idempotent_calls(self) -> None:
        """Multiple configure_logging calls don't stack handlers."""
        configure_logging(verbose=True, log_json=False)
        configure_logging(verbose=True, log_json=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1
