"""
No create/update/delete endpoints: Fines are entirely system-generated
by FineService (from LoanService.return_book() and the daily
calculate_fines command), never created directly through this API.

`pay` is a member-only transaction: the owning member goes through the
(mock) payment gateway with the card details in the request body, per
FineService.pay_online. Admins can view every fine (list/retrieve) and
`waive` a fine as a discretionary write-off, but they don't pay fines
on a member's behalf — that keeps "money changed hands" auditable as
something only the member themselves triggers.

`waive` stays admin-only — that's a discretionary write-off, not a
payment, so there's no member-facing equivalent.
"""

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsMember, IsOwnerOrAdmin

from .gateway import PaymentDeclined
from .models import Fine
from .serializers import FineSerializer, PaymentSerializer
from .services import FineService


class FineViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/v1/fines/              -> list (own fines for members, all for admins)
    GET  /api/v1/fines/{id}/         -> retrieve (own, or any for admins)
    POST /api/v1/fines/{id}/pay/     -> member (owner) only: pay online, body {"card_number": "..."}
    POST /api/v1/fines/{id}/waive/   -> waive the fine (admin only)
    GET  /api/v1/fines/{id}/payments/ -> payment attempt history for this fine
    """

    serializer_class = FineSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):

        if getattr(self, "swagger_fake_view", False):
            return Fine.objects.none()

        user = self.request.user
        qs = Fine.objects.select_related("user", "loan", "loan__book")
        if user.role == user.Roles.ADMIN:
            return qs
        return qs.filter(user=user)

    def get_permissions(self):
        if self.action == "waive":
            return [permissions.IsAuthenticated(), IsAdmin()]
        if self.action == "pay":
            return [permissions.IsAuthenticated(), IsMember(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        fine = self.get_object()
        if fine.status != Fine.Status.UNPAID:
            return Response(
                {"detail": f"Fine is already {fine.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        card_number = request.data.get("card_number")
        if not card_number:
            return Response(
                {"detail": "card_number is required to pay online."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            FineService.pay_online(fine=fine, user=request.user, card_number=card_number)
        except PaymentDeclined as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED
            )

        return Response(FineSerializer(fine).data)

    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        fine = self.get_object()
        if fine.status != Fine.Status.UNPAID:
            return Response(
                {"detail": f"Fine is already {fine.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FineService.waive(fine)
        return Response(FineSerializer(fine).data)

    @action(detail=True, methods=["get"])
    def payments(self, request, pk=None):
        fine = self.get_object()
        serializer = PaymentSerializer(fine.payments.all(), many=True)
        return Response(serializer.data)