from django.contrib import admin

from apps.logs.models import LogEntry


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("level", "message", "ip_address", "request_path", "created_at")
    list_filter = ("level", "created_at")
    search_fields = ("message", "request_path")


admin.site.register(LogEntry, LogEntryAdmin)
