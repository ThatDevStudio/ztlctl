"""structlog configuration for ztlctl.

Two output modes:
- Human (default): Rich-formatted colored output to stderr
- JSON (--log-json): Structured JSON lines to stderr
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(
    *,
    verbose: bool = False,
    log_json: bool = False,
) -> None:
    """Configure structlog processors and output routing.

    Args:
        verbose: Enable DEBUG-level output. When False, only WARNING+.
        log_json: Use JSON renderer instead of console renderer.
    """
    ztl_level = logging.DEBUG if verbose else logging.WARNING

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    ztl_logger = logging.getLogger("ztlctl")
    ztl_logger.setLevel(ztl_level)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("copier").setLevel(logging.WARNING)
