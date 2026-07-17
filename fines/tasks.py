"""
(see core/celery.py's beat_schedule for the "daily at 01:00" trigger).

The management command at fines/management/commands/calculate_fines.py
is left in place — it's still handy for manually re-running the job or
for debugging without touching the scheduler.
"""

import logging

from celery import shared_task
from django.utils import timezone

from fines.services import FineService
from loans.models import Loan

logger = logging.getLogger(__name__)


@shared_task(name="fines.tasks.calculate_fines_task")
def calculate_fines_task():
    """
    Transitions ACTIVE loans past their due_date to OVERDUE and
    creates/updates their fines. Idempotent — safe to re-run.
    """
    today = timezone.localdate()

    overdue_loans = Loan.objects.filter(
        status__in=[Loan.Status.ACTIVE, Loan.Status.OVERDUE],
        due_date__lt=today,
    ).select_related("user", "book")

    transitioned = 0
    fines_touched = 0

    for loan in overdue_loans:
        if loan.status != Loan.Status.OVERDUE:
            loan.status = Loan.Status.OVERDUE
            loan.save(update_fields=["status"])
            transitioned += 1

        fine = FineService.recalculate_fine_for_active_loan(loan)
        if fine is not None:
            fines_touched += 1

    logger.info(
        "calculate_fines_task: transitioned %s loan(s) to OVERDUE; "
        "created/updated %s fine(s).",
        transitioned,
        fines_touched,
    )
    return {"transitioned": transitioned, "fines_touched": fines_touched}