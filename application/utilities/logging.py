import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from application.utilities.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id


def setup_logging() -> logging.Logger:
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("event_rsvp")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    if logger.handlers:
        logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


logger = setup_logging()
