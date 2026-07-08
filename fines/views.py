"""
No create/update/delete endpoints: Fines are entirely system-generated
by FineService (from LoanService.return_book() and the daily
calculate_fines command), never created directly through this API.

`pay`/`waive` are admin-only for now. The handover doc mentions Phase 9
("mark paid ... or via payment flow in Phase 8") may add a member-facing
payment flow later — when that lands, `pay` likely needs to branch on
who's calling it (admin manually marking paid vs. a payment webhook
confirming a real transaction), but that's out of scope here.
"""

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdmin, IsOwnerOrAdmin

from .models import Fine
from .serializers import FineSerializer
from .services import FineService


class FineViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/v1/fines/            -> list (own fines for members, all for admins)
    GET  /api/v1/fines/{id}/       -> retrieve (own, or any for admins)
    POST /api/v1/fines/{id}/pay/   -> mark as paid (admin only)
    POST /api/v1/fines/{id}/waive/ -> waive the fine (admin only)
    """

    serializer_class = FineSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Fine.objects.select_related("user", "loan", "loan__book")
        if user.role == user.Roles.ADMIN:
            return qs
        return qs.filter(user=user)

    def get_permissions(self):
        if self.action in ("pay", "waive"):
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        fine = self.get_object()
        if fine.status != Fine.Status.UNPAID:
            return Response(
                {"detail": f"Fine is already {fine.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FineService.mark_paid(fine)
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