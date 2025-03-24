from django.contrib import admin
from apps.etc.models import Developer

# Register your models here.
@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    search_fields = ("name", "email")
    ordering = ("name",)