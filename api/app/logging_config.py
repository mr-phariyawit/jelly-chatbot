"""
Structured JSON Logging Configuration
Outputs JSON logs in production (Cloud Run → Cloud Logging) and human-readable logs in development.
"""

import os
import sys
import logging
import json
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON for Cloud Logging / structured log ingestion.
    Follows Google Cloud Logging severity levels.
    """

    SEVERITY_MAP = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARNING": "WARNING",
        "ERROR": "ERROR",
        "CRITICAL": "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": self.SEVERITY_MAP.get(record.levelname, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if provided via `extra={}` in log calls
        for key in ("bot_id", "user_id", "event_type", "latency_ms", "request_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = record.levelname.ljust(7)
        return f"{timestamp} {level} [{record.name}] {record.getMessage()}"


def setup_logging():
    """
    Configure logging for the application.
    Uses JSON in production (Cloud Run), human-readable in development.
    """
    is_production = bool(os.getenv("K_SERVICE"))
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevFormatter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
