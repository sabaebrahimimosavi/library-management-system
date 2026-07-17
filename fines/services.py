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

`pay_online` is the member-facing counterpart to the admin-only
`mark_paid`/`waive` pair below: it goes through the (mock) payment
gateway and records a Payment attempt row regardless of outcome, so a
declined card doesn't just disappear.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from notifications.services import NotificationService

from .gateway import MockPaymentGateway, PaymentDeclined
from .models import Fine, Payment

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

    @classmethod
    @transaction.atomic
    def mark_paid(cls, fine):
        fine.status = Fine.Status.PAID
        fine.paid_at = timezone.now()
        fine.save(update_fields=["status", "paid_at", "updated_at"])

        # A fine can exist for a loan that's still ACTIVE/OVERDUE (the daily
        # calculate_fines job fines loans before they're returned). If the
        # member pays it off before physically returning the book, treat
        # the payment as closing the loan out too — otherwise the loan
        # would stay open forever with no way to reconcile it.
        loan = fine.loan
        if loan.status != loan.Status.RETURNED:
            # Local import: loans.services already imports fines.services
            # at module level, so importing LoanService up top here would
            # be a circular import.
            from loans.services import LoanService

            LoanService.return_book(loan=loan)

        return fine

    @classmethod
    def pay_online(cls, *, fine, user, card_number):
        """
        Member-facing self-service payment, routed through the (mock)
        payment gateway. Always records a Payment row — SUCCEEDED or
        FAILED — so a declined attempt leaves an audit trail instead of
        silently vanishing. Only marks the Fine PAID on success.

        Raises PaymentDeclined if the gateway declines the charge; the
        Fine is left UNPAID (and can be retried) in that case.

        Callers (the view) are responsible for checking
        `fine.status == UNPAID` before calling this — this method
        doesn't re-check, since the view already holds the object via
        IsOwnerOrAdmin and this shouldn't run at all against a
        already-settled fine.
        """
        result = MockPaymentGateway.charge(amount=fine.amount, card_number=card_number)

        payment = Payment.objects.create(
            fine=fine,
            user=user,
            amount=fine.amount,
            method=Payment.Method.CARD,
            status=Payment.Status.SUCCEEDED if result["success"] else Payment.Status.FAILED,
            provider_reference=result["reference"],
        )

        if not result["success"]:
            raise PaymentDeclined("Payment was declined. Please try a different card.")

        cls.mark_paid(fine)
        NotificationService.notify_fine_paid(fine)
        return payment

    @staticmethod
    def waive(fine):
        fine.status = Fine.Status.WAIVED
        fine.waived_at = timezone.now()
        fine.save(update_fields=["status", "waived_at", "updated_at"])
        return fine