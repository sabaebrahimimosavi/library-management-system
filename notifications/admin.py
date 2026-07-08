"""
notifications/admin.py
"""

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "notification_type",
        "channel",
        "status",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "channel", "status", "is_read")
    search_fields = ("user__username", "user__email", "subject", "message")
    readonly_fields = (
        "user",
        "notification_type",
        "channel",
        "subject",
        "message",
        "sent_at",
        "failure_reason",
        "loan",
        "reservation",
        "created_at",
        "updated_at",
    )
