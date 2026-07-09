from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self):
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"refresh": "Invalid or expired refresh token."}
            )

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the authenticated user's own profile.
    Used by GET/PATCH /api/v1/auth/me/.

    `role` and `date_joined` are read-only here: role changes must go
    through a dedicated admin-only endpoint in a later phase, not through
    self-service profile updates.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
        )
        read_only_fields = ("id", "role", "date_joined")

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """POST body for /api/v1/auth/password-reset/"""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """POST body for /api/v1/auth/password-reset/confirm/"""

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    POST body for /api/v1/auth/change-password/
    Requires the authenticated user's current password for confirmation.
    """

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        return user


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the admin-only member list/management endpoints.
    Read-heavy: role changes go through AdminUserRoleSerializer's
    dedicated endpoint instead of being PATCH-able here, so the list
    endpoint stays list-only (no accidental writes from a GET view).
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "date_joined",
        )
        read_only_fields = fields


class AdminUserRoleSerializer(serializers.Serializer):
    """POST/PATCH body for /api/v1/auth/users/{id}/role/"""

    role = serializers.ChoiceField(choices=User.Roles.choices)