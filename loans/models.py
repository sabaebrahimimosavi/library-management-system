from django.conf import settings
from django.db import models
from django.utils import timezone

from books.models import Book


class Loan(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"
        OVERDUE = "OVERDUE", "Overdue"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name="loans",
    )

    borrowed_at = models.DateTimeField(
        auto_now_add=True
    )

    due_date = models.DateField()

    returned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-borrowed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"