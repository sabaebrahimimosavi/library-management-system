from django.shortcuts import render


class DjangoAdminAccessMiddleware:
    """
    Allow /django-admin/ only for an authenticated
    Django session belonging to a library administrator.

    Everyone else receives a permission-denied page
    instead of the standard Django Admin login page.
    """

    ADMIN_PREFIX = "/django-admin/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_path = (
            request.path == "/django-admin"
            or request.path.startswith(
                self.ADMIN_PREFIX
            )
        )

        if is_admin_path:
            user = request.user

            is_allowed = (
                user.is_authenticated
                and user.is_active
                and user.is_staff
                and (
                    getattr(
                        user,
                        "role",
                        None,
                    ) == "ADMIN"
                    or user.is_superuser
                )
            )

            if not is_allowed:
                return render(
                    request,
                    (
                        "accounts/"
                        "admin_permission_denied.html"
                    ),
                    status=403,
                )

        return self.get_response(request)