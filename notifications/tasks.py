"""
notifications/tasks.py

Celery task replacing the manual
`python manage.py send_due_date_reminders` command. Same logic, just
triggered by Celery Beat instead of a human (see core/celery.py's
beat_schedule for the "daily at 08:00" trigger).

The management command at
notifications/management/commands/send_due_date_reminders.py is left in
place for manual/debug use.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from loans.models import Loan
from notifications.services import NotificationService

logger = logging.getLogger(__name__)


@shared_task(name="notifications.tasks.send_due_date_reminders_task")
def send_due_date_reminders_task():
    """
    Sends 'due in 2 days' and 'due today' reminder notifications/emails
    for all currently ACTIVE loans. Idempotent — NotificationService
    checks for an existing notification per loan per reminder type
    before sending, so re-running the same day won't double-send.
    """
    today = timezone.localdate()
    two_days_out = today + timedelta(days=2)

    due_soon_loans = Loan.objects.filter(
        status=Loan.Status.ACTIVE, due_date=two_days_out
    ).select_related("user", "book")
    due_today_loans = Loan.objects.filter(
        status=Loan.Status.ACTIVE, due_date=today
    ).select_related("user", "book")

    sent_count = 0

    for loan in due_soon_loans:
        if NotificationService.notify_due_soon(loan) is not None:
            sent_count += 1

    for loan in due_today_loans:
        if NotificationService.notify_due_today(loan) is not None:
            sent_count += 1

    logger.info(
        "send_due_date_reminders_task: checked %s due-soon and %s "
        "due-today loan(s); sent %s new reminder notification(s).",
        due_soon_loans.count(),
        due_today_loans.count(),
        sent_count,
    )
    return {"sent": sent_count}