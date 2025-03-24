import logging
from apps.logs.models import LogEntry
from constants.constants import LOG_LEVELS

logger = logging.getLogger("django")


def log_message(app,level, message, request=None):
    """Log messages to both console and database."""
    log_level = LOG_LEVELS.get(level, logging.INFO)
    logger.log(log_level, message, extra={"request": request})
    LogEntry.objects.create(
        level=level,
        message=message,
        app=app,
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        request_path=request.path if request else None,
    )