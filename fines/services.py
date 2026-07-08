"""
Two entry points, called from two different places, both funneling into
the same private upsert logic:

- `finalize_fine_on_return(loan)` — called from LoanService.return_book()
  at the moment a loan is returned. Uses the actual return date, so a
  fine is fixed at whatever it was on the day the book came back and
  never grows afterward.
- `recalculate_fine_for_active_loan(loan)` — called from the daily
  `calculate_fines` management command for loans that are overdue but
  NOT yet returned. Uses today's date, so the fine keeps growing each
  day the book stays out.

This two-entry-point split (rather than a single always-run-daily job)
means a fine is correct immediately on return instead of waiting for the
next day's cron/scheduled run — worth noting since the handover doc
suggested "the same scheduled job" for overdue-detection and fine
calculation; this keeps that job for the still-active/overdue case but
finalizes eagerly on return since that hook point already exists in
LoanService.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from notifications.services import NotificationService

from .models import Fine

DEFAULT_DAILY_FINE_AMOUNT = "0.50"


class FineService:
    @staticmethod
    def _daily_rate() -> Decimal:
        return Decimal(
            str(getattr(settings, "DAILY_FINE_AMOUNT", DEFAULT_DAILY_FINE_AMOUNT))
        )

    @classmethod
    @transaction.atomic
    def _upsert_fine(cls, *, loan, reference_date, daily_rate=None):
        """
        Creates or updates the Fine for `loan` based on how many days past
        `loan.due_date` the given `reference_date` is.

        Never touches a fine that's already PAID or WAIVED — those are
        considered settled and shouldn't change even if this is called
        again. Returns None if there's no overdue period (nothing to fine).
        """
        overdue_days = (reference_date - loan.due_date).days
        if overdue_days <= 0:
            return None

        rate = daily_rate if daily_rate is not None else cls._daily_rate()
        amount = rate * overdue_days

        fine = Fine.objects.filter(loan=loan).first()

        if fine is not None:
            if fine.status != Fine.Status.UNPAID:
                return fine  # already settled; leave it alone
            if fine.overdue_days != overdue_days or fine.amount != amount:
                fine.overdue_days = overdue_days
                fine.amount = amount
                fine.daily_rate = rate
                fine.save(
                    update_fields=["overdue_days", "amount", "daily_rate", "updated_at"]
                )
            return fine

        fine = Fine.objects.create(
            loan=loan,
            user=loan.user,
            overdue_days=overdue_days,
            daily_rate=rate,
            amount=amount,
        )
        NotificationService.notify_fine_issued(fine)
        return fine

    @classmethod
    def recalculate_fine_for_active_loan(cls, loan):
        return cls._upsert_fine(loan=loan, reference_date=timezone.localdate())

    @classmethod
    def finalize_fine_on_return(cls, loan):
        reference_date = (loan.returned_at or timezone.now()).date()
        return cls._upsert_fine(loan=loan, reference_date=reference_date)

    @staticmethod
    def mark_paid(fine):
        fine.status = Fine.Status.PAID
        fine.paid_at = timezone.now()
        fine.save(update_fields=["status", "paid_at", "updated_at"])
        return fine

    @staticmethod
    def waive(fine):
        fine.status = Fine.Status.WAIVED
        fine.waived_at = timezone.now()
        fine.save(update_fields=["status", "waived_at", "updated_at"])
        return fine
