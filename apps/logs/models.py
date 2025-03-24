from django.db import models
from django.utils.translation import gettext_lazy as _

class LogLevel(models.TextChoices):
    """Log Levels"""
    INFO = "Info", _("Info")
    WARNING = "Warning", _("Warning")
    ERROR = "Error", _("Error")
    DEBUG = "Debug", _("Debug")
    CRITICAL = "Critical", _("Critical")



class LogEntry(models.Model):
    level = models.CharField(max_length=10, choices=LogLevel.choices, default=LogLevel.INFO)
    app = models.CharField(max_length=255,default="")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.level}: {self.message[:50]} ({self.created_at})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Log entries"