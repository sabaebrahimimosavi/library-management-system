from rest_framework import permissions

from accounts.models import User


class IsReservationOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: only the reservation's owner or an admin
    may retrieve or cancel a reservation.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Roles.ADMIN:
            return True
        return obj.user_id == request.user.id
