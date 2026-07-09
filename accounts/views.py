from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import User
from .permissions import IsAdmin
from .serializers import (
    AdminUserRoleSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)
from .services import PasswordResetService


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/auth/me/
    PATCH /api/v1/auth/me/
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use PATCH for partial profile updates."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class PasswordResetRequestThrottle(AnonRateThrottle):
    scope = "password_reset"


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PasswordResetService.send_reset_email(
            serializer.validated_data["email"]
        )

        return Response(
            {"detail": "If that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/confirm/
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        success = PasswordResetService.reset_password(
            **serializer.validated_data
        )

        if not success:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    """
    POST /api/v1/auth/change-password/
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(
            serializer.validated_data["new_password"]
        )
        request.user.save(update_fields=["password"])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class LogoutView(generics.GenericAPIView):
    """
    POST /api/v1/auth/logout/
    """

    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class UserListView(generics.ListAPIView):
    """
    GET /api/v1/auth/users/?search=&role=

    Admin-only member directory. Filtering is done manually (not via
    filterset_fields/DjangoFilterBackend) to match how this project
    already handles ad-hoc query params elsewhere — see the "Known
    backend gaps" note about LoanViewSet/NotificationViewSet for the
    reasoning; there's no need to introduce a new pattern just for this
    one list endpoint.
    """

    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role.upper())

        return qs


class UserRoleUpdateView(generics.GenericAPIView):
    """
    PATCH /api/v1/auth/users/{id}/role/   body: {"role": "ADMIN" | "MEMBER"}

    Admin-only. Promotes/demotes a member. An admin can't change their
    own role through this endpoint — that's a deliberate guardrail
    against a solo admin locking themselves out; role changes to the
    caller's own account still go through the Django admin site.
    """

    serializer_class = AdminUserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = User.objects.all()

    def patch(self, request, *args, **kwargs):
        target = self.get_object()

        if target.pk == request.user.pk:
            return Response(
                {"detail": "You can't change your own role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target.role = serializer.validated_data["role"]
        target.save(update_fields=["role"])

        return Response(AdminUserSerializer(target).data)