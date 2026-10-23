from django.contrib import admin

from .models import RowError, ValidationRun


class RowErrorInline(admin.TabularInline):
    model = RowError
    extra = 0


@admin.register(ValidationRun)
class ValidationRunAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "source", "total_rows", "invalid_rows", "created_at")
    list_filter = ("source",)
    inlines = [RowErrorInline]
