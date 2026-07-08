"""
notifications/models.py
"""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    A record of a single notification sent (or attempted) to a user.

    Kept as concrete FKs to Loan/Reservation rather than a GenericForeignKey
    — there are only two notification-worthy sources right now, and explicit
    FKs are easier to query, migrate, and reason about than a generic
    relation for this scale of app.
    """

    class NotificationType(models.TextChoices):
        DUE_SOON_REMINDER = "DUE_SOON_REMINDER", "Due in 2 Days"
        DUE_TODAY_REMINDER = "DUE_TODAY_REMINDER", "Due Today"
        RESERVATION_AVAILABLE = "RESERVATION_AVAILABLE", "Reservation Available"
        FINE_ISSUED = "FINE_ISSUED", "Fine Issued"
        FINE_PAID = "FINE_PAID", "Fine Paid"
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices
    )
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.EMAIL
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    # Optional links back to the record that triggered the notification.
    # SET_NULL so deleting a loan/reservation doesn't delete notification
    # history — the message text stands on its own.
    loan = models.ForeignKey(
        "loans.Loan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type", "loan"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.user} [{self.status}]"
