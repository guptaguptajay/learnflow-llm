"""Logging configuration with structured logging support."""

import logging
import sys
from typing import Any

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Add correlation ID if present
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            record.msg = f"[{correlation_id}] {record.msg}"
        return super().format(record)


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for module."""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding correlation IDs."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Process log message with extra context."""
        extra = kwargs.get("extra", {})
        if "correlation_id" in self.extra:
            extra["correlation_id"] = self.extra["correlation_id"]
        kwargs["extra"] = extra
        return msg, kwargs

