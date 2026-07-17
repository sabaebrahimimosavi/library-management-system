"""
Role-based access control for the Library Management System.

"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allows access only to users with the ADMIN role."""

    message = "Only administrators are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == request.user.Roles.ADMIN
        )


class IsMember(permissions.BasePermission):
    """Allows access only to users with the MEMBER role."""

    message = "Only members are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == request.user.Roles.MEMBER
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Any authenticated user may read (GET/HEAD/OPTIONS).
    Only ADMIN users may write (POST/PUT/PATCH/DELETE).

    Useful for catalog resources (books, authors, genres, publishers) in
    upcoming phases, where members browse but only admins curate.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == request.user.Roles.ADMIN


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: grants access if the requesting user owns the
    object (via a `user` or `owner` attribute on the model instance) or if
    the requesting user is an administrator.

    Useful for apps (loans, reservations, reviews, payments) where
    members should only see/modify their own records.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == request.user.Roles.ADMIN:
            return True

        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user