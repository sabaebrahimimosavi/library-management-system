from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Reservation


class ReservationService:
    """
    Business logic for reserving unavailable books, cancelling
    reservations, and advancing the reservation queue.
    """

    @staticmethod
    @transaction.atomic
    def reserve_book(user, book):
        if book.available_copies > 0:
            raise ValidationError(
                "Book is currently available. Please borrow it instead of reserving."
            )

        already_pending = Reservation.objects.filter(
            user=user, book=book, status=Reservation.Status.PENDING
        ).exists()
        if already_pending:
            raise ValidationError(
                "You already have a pending reservation for this book."
            )

        return Reservation.objects.create(user=user, book=book)

    @staticmethod
    @transaction.atomic
    def cancel_reservation(reservation):
        if reservation.status != Reservation.Status.PENDING:
            raise ValidationError("Only pending reservations can be cancelled.")

        reservation.status = Reservation.Status.CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save(update_fields=["status", "cancelled_at"])
        return reservation

    @staticmethod
    @transaction.atomic
    def get_next_pending_reservation(book):
        return (
            Reservation.objects.filter(
                book=book,
                status=Reservation.Status.PENDING,
            )
            .order_by("reserved_at")
            .first()
        )

    @staticmethod
    @transaction.atomic
    def mark_fulfilled(reservation):
        if reservation.status != Reservation.Status.PENDING:
            raise ValidationError(
                "Only pending reservations can be fulfilled."
            )
        reservation.status = Reservation.Status.FULFILLED
        reservation.fulfilled_at = timezone.now()
        reservation.save(update_fields=["status", "fulfilled_at"])
        return reservation

    @staticmethod
    def get_pending_reservations(*, book):
        """
        Returns ALL pending reservations for `book`, oldest first.
 
        Used by LoanService.return_book() to notify every waiting member
        when a copy becomes available — not just the head of the queue,
        since whoever actually shows up to borrow it doesn't have to be
        the first person who reserved it.
        """
        return Reservation.objects.filter(
            book=book, status=Reservation.Status.PENDING
        ).order_by("reserved_at")
 
    @staticmethod
    def get_pending_reservation_for_user(*, book, user):
        """
        Returns this user's own PENDING reservation for `book`, if any,
        else None.
 
        Used by LoanService.borrow_book() to detect that a borrowing
        member is acting on their own reservation, so it can be marked
        fulfilled (removing it from the pending queue) at the moment
        they actually borrow — not when they were merely notified.
        """
        return Reservation.objects.filter(
            book=book, user=user, status=Reservation.Status.PENDING
        ).first()