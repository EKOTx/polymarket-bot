"""
Structured logging setup.
Outputs JSON to file, pretty to console.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

import structlog
from rich.logging import RichHandler


def setup_logging(level: str = "INFO", log_file: str = "logs/scanner.log") -> None:
    """Configure structlog + stdlib logging."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Stdlib handlers
    handlers: list[logging.Handler] = [
        RichHandler(rich_tracebacks=True, show_path=False, markup=True),
    ]

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    handlers.append(file_handler)

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=handlers,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a named structlog logger."""
    return structlog.get_logger(name)
