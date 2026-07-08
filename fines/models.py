"""
Design decision: one Fine per Loan (OneToOneField), not one row per
overdue day. FineService recalculates `overdue_days`/`amount` in place on
the same row while the loan is still out, and freezes it the moment the
loan is returned or the fine is paid/waived. The handover doc's
"Fine model: loan (FK)..." doesn't specify uniqueness explicitly — this
picks the simpler of the two reasonable designs (one evolving record vs.
a per-day ledger) since nothing in Phase 5's requirements needs a
historical ledger of daily fine increments, only the current total.
"""

from django.conf import settings
from django.db import models


class Fine(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PAID = "PAID", "Paid"
        WAIVED = "WAIVED", "Waived"

    loan = models.OneToOneField(
        "loans.Loan",
        on_delete=models.PROTECT,
        related_name="fine",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fines",
    )

    overdue_days = models.PositiveIntegerField(default=0)
    daily_rate = models.DecimalField(max_digits=6, decimal_places=2)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.UNPAID
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    waived_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Fine(loan={self.loan_id}) {self.amount} [{self.status}]"