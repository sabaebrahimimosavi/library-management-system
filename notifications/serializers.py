"""
notifications/serializers.py
"""

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Read-focused serializer for a user's notification feed. Notifications
    are system-generated, so almost everything here is read-only; the one
    thing a member can change is `is_read`, handled by a dedicated action
    rather than a general update endpoint (see NotificationViewSet).
    """

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    channel_display = serializers.CharField(
        source="get_channel_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "notification_type",
            "notification_type_display",
            "channel",
            "channel_display",
            "status",
            "status_display",
            "subject",
            "message",
            "is_read",
            "sent_at",
            "loan",
            "reservation",
            "created_at",
        )
        read_only_fields = (
            "id",
            "notification_type",
            "channel",
            "status",
            "subject",
            "message",
            "sent_at",
            "loan",
            "reservation",
            "created_at",
        )
