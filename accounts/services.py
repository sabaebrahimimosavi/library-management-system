"""
Business logic for authentication-adjacent workflows, kept out of views
and serializers per the project's "no business logic in views / no fat
serializers" rule.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class PasswordResetService:
    """Encapsulates the password-reset request/confirm workflow."""

    @staticmethod
    def _generate_reset_link(user, frontend_base_url: str) -> str:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        # The frontend uses hash-based routing (createWebHashHistory), so
        # the link needs a `#` before the route path or Vue Router never
        # sees it and the SPA just loads its default route.
        return f"{frontend_base_url}/#/reset-password/{uidb64}/{token}"

    @classmethod
    def send_reset_email(cls, email: str, frontend_base_url: str = None) -> None:
        """
        Sends a reset email if the address matches a user. Silently no-ops
        otherwise, so the API response never reveals whether an email is
        registered (mitigates user enumeration).
        """
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        frontend_base_url = frontend_base_url or getattr(
            settings, "FRONTEND_BASE_URL", "http://localhost:3000"
        )
        reset_link = cls._generate_reset_link(user, frontend_base_url)

        send_mail(
            subject="Reset your Library account password",
            message=(
                f"Hello {user.username},\n\n"
                f"Use the link below to reset your password:\n{reset_link}\n\n"
                "This link will expire automatically for security reasons.\n"
                "If you did not request this, you can safely ignore this email."
            ),
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "no-reply@library.local"
            ),
            recipient_list=[user.email],
            fail_silently=True,
        )

    @staticmethod
    def get_user_from_uid(uidb64: str):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    @classmethod
    def validate_token(cls, uidb64: str, token: str):
        user = cls.get_user_from_uid(uidb64)
        if user is None:
            return None
        if not token_generator.check_token(user, token):
            return None
        return user

    @classmethod
    def reset_password(cls, uidb64: str, token: str, new_password: str) -> bool:
        user = cls.validate_token(uidb64, token)
        if user is None:
            return False
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return True