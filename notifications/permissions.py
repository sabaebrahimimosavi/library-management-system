from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Members may only access their own notifications. Admins may access
    everyone's. Mirrors accounts.permissions.IsOwnerOrAdmin, duplicated
    locally so the notifications app has no import dependency on accounts
    beyond the User model itself.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == request.user.Roles.ADMIN:
            return True
        return obj.user == request.user
