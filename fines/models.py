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


class Payment(models.Model):
    """
    One row per payment *attempt* against a Fine, not one row per Fine —
    a declined card retry shouldn't overwrite or discard the failed
    attempt. `FineService.pay_online` is the only writer; it creates a
    SUCCEEDED or FAILED row for every gateway call and only marks the
    parent Fine PAID on success. `fine.payments.all()` gives the full
    attempt history for support/audit purposes.
    """

    class Status(models.TextChoices):
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    class Method(models.TextChoices):
        CARD = "CARD", "Card"

    fine = models.ForeignKey(
        Fine,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fine_payments",
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(
        max_length=10, choices=Method.choices, default=Method.CARD
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    # Opaque ID from the gateway (mock for now). Not unique — a real
    # gateway may reuse/retry references on its own terms.
    provider_reference = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["fine", "status"]),
        ]

    def __str__(self):
        return f"Payment(fine={self.fine_id}) {self.amount} [{self.status}]"