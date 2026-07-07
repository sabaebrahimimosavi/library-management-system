from django.db import transaction
from django.utils import timezone

from .models import Loan




class LoanService:

    @staticmethod
    @transaction.atomic
    def borrow_book(*, user, book, due_date):

        if book.available_copies <= 0:
            raise ValueError("Book is not available.")

        loan = Loan.objects.create(
            user=user,
            book=book,
            due_date=due_date,
        )

        book.available_copies -= 1
        book.save(update_fields=["available_copies"])

        return loan

    @staticmethod
    @transaction.atomic
    def return_book(*, loan):

        if loan.status != Loan.Status.ACTIVE:
            raise ValueError("This loan is already closed.")

        loan.status = Loan.Status.RETURNED
        loan.returned_at = timezone.now()

        loan.save(
            update_fields=[
                "status",
                "returned_at",
            ]
        )

        book = loan.book
        book.available_copies += 1

        book.save(
            update_fields=[
                "available_copies",
            ]
        )

        next_reservation = ReservationService.get_next_pending_reservation(book)

        if next_reservation:
            NotificationService.notify_book_available(next_reservation)

        return loan