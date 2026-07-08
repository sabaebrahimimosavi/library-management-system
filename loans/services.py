from django.db import transaction
from django.utils import timezone
 
from notifications.services import NotificationService
from reservations.services import ReservationService
 
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

        own_pending_reservation = ReservationService.get_pending_reservation_for_user(
            book=book, user=user
        )
        if own_pending_reservation is not None:
            ReservationService.mark_fulfilled(own_pending_reservation)

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

        pending_reservations = ReservationService.get_pending_reservations(book=book)
       
        for reservation in pending_reservations:
            NotificationService.notify_reservation_available(reservation)
        
        return loan