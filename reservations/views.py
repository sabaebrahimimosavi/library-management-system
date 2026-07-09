from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from books.models import Book

from .models import Reservation
from .permissions import IsReservationOwnerOrAdmin
from .serializers import ReservationSerializer
from .services import ReservationService


def _validation_error_detail(exc: DjangoValidationError):
    messages = getattr(exc, "messages", None)
    return messages[0] if messages else str(exc)


class ReservationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Members can create reservations for unavailable books, view their own
    reservations, and cancel them. Admins can view every reservation.
    No direct update/delete — state changes only happen through services.
    """

    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsReservationOwnerOrAdmin]

    def get_queryset(self):

        if getattr(self, "swagger_fake_view", False):
            return Reservation.objects.none()

        user = self.request.user
        if user.role == User.Roles.ADMIN:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        book = Book.objects.filter(pk=request.data.get("book")).first()
        if book is None:
            return Response(
                {"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            reservation = ReservationService.reserve_book(user=request.user, book=book)
        except DjangoValidationError as exc:
            return Response(
                {"detail": _validation_error_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        try:
            reservation = ReservationService.cancel_reservation(reservation)
        except DjangoValidationError as exc:
            return Response(
                {"detail": _validation_error_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(reservation)
        return Response(serializer.data, status=status.HTTP_200_OK)
