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