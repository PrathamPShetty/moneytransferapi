import logging
from django.utils.timezone import now
class DBHandler(logging.Handler):
    """Custom logging handler that stores logs in the database."""

    def emit(self, record):
        try:
            from apps.logs.models import LogEntry  # Import here to prevent circular import issues

            log = LogEntry(
                level=record.levelname,
                message=record.getMessage(),
                app=record.name,
                created_at=now(),
            )
            log.save()
        except Exception as e:
            # Fallback in case of an error (avoid breaking Django startup)
            print(f"Logging error: {e}")