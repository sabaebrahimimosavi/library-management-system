"""
Responsibilities :
  1. Find ACTIVE loans whose due_date has passed and transition them to
     OVERDUE .
  2. Recalculate/create the running Fine for each of those loans, using
     today's date — so the fine keeps growing the longer the book stays
     unreturned.

Loans returned late are NOT handled here — those are finalized
immediately in LoanService.return_book() via
FineService.finalize_fine_on_return(), since that hook already fires at
the right moment and doesn't need to wait for this daily job.

"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from fines.services import FineService
from loans.models import Loan


class Command(BaseCommand):
    help = (
        "Transitions ACTIVE loans past their due_date to OVERDUE and "
        "creates/updates their fines. Run once daily."
    )

    def handle(self, *args, **options):
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Transitioned {transitioned} loan(s) to OVERDUE; "
                f"created/updated {fines_touched} fine(s)."
            )
        )
