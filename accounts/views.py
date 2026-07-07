from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    UserSerializer
)
from .services import PasswordResetService


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/auth/me/   -> current authenticated user's profile
    PATCH /api/v1/auth/me/   -> partial update (first_name, last_name, email)

    PUT is intentionally disabled: full-replacement doesn't make sense for
    a profile endpoint with read-only fields like `role`.
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


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — request a reset email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordResetService.send_reset_email(serializer.validated_data["email"])
        # Always 200, regardless of whether the email exists (anti-enumeration).
        return Response(
            {"detail": "If that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — set a new password."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        success = PasswordResetService.reset_password(**serializer.validated_data)
        if not success:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/ — authenticated password change."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(
            {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
        )

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
