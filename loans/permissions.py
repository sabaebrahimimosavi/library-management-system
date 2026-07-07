from rest_framework import permissions

class IsLoanOwnerOrAdmin(
    permissions.BasePermission
):

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):

        if request.user.role == request.user.Roles.ADMIN:
            return True

        return obj.user == request.user

