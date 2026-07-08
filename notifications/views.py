"""
notifications/views.py

Views stay thin: queryset scoping and a single state change (mark as
read), nothing else. Notification creation happens exclusively through
NotificationService, never through this API.
"""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .permissions import IsOwnerOrAdmin
from .serializers import NotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/v1/notifications/            -> list (own, or all for admins)
    GET  /api/v1/notifications/{id}/       -> retrieve (own, or any for admins)
    POST /api/v1/notifications/{id}/read/  -> mark as read

    No create/update/delete endpoints: notifications are system-generated
    via NotificationService and are otherwise immutable except for the
    read flag.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Roles.ADMIN:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
