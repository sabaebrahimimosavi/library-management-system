"""
notifications/management/commands/send_due_date_reminders.py

Intended to run once per day (via cron, celery-beat, or a scheduled task
runner). Idempotent: safe to re-run the same day without double-sending,
since NotificationService checks for an existing notification per loan
per reminder type before sending.

Example crontab entry (runs daily at 08:00 server time):
    0 8 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_due_date_reminders
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from loans.models import Loan
from notifications.services import NotificationService


class Command(BaseCommand):
    help = (
        "Sends 'due in 2 days' and 'due today' reminder notifications "
        "for all currently ACTIVE loans."
    )

    def handle(self, *args, **options):
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {due_soon_loans.count()} due-soon and "
                f"{due_today_loans.count()} due-today loan(s); "
                f"sent {sent_count} new reminder notification(s)."
            )
        )