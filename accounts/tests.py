"""
Covers:
  - Model tests (User)
  - Serializer tests (UserProfileSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer)
  - API tests (register, login, refresh, me GET/PATCH, password reset
    request/confirm, change password)
  - Permission tests (IsAdmin, IsMember, IsAdminOrReadOnly, IsOwnerOrAdmin)
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from .permissions import IsAdmin, IsAdminOrReadOnly, IsMember, IsOwnerOrAdmin
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class UserModelTests(TestCase):
    def test_create_user_defaults_to_member_role(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.assertEqual(user.role, User.Roles.MEMBER)

    def test_create_superuser_role_can_be_admin(self):
        admin = User.objects.create_superuser(
            username="root", email="root@example.com", password="StrongPass123!"
        )
        admin.role = User.Roles.ADMIN
        admin.save()
        self.assertEqual(admin.role, User.Roles.ADMIN)
        self.assertTrue(admin.is_superuser)

    def test_string_representation_is_email(self):
        user = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )
        self.assertEqual(str(user), "bob@example.com")

    def test_email_uniqueness_enforced(self):
        User.objects.create_user(
            username="carol", email="dup@example.com", password="StrongPass123!"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="carol2", email="dup@example.com", password="StrongPass123!"
            )


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------
class UserProfileSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dave", email="dave@example.com", password="StrongPass123!"
        )
        self.other = User.objects.create_user(
            username="erin", email="erin@example.com", password="StrongPass123!"
        )

    def test_role_is_read_only(self):
        serializer = UserProfileSerializer(
            self.user, data={"role": User.Roles.ADMIN}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        self.assertEqual(updated.role, User.Roles.MEMBER)  # unchanged

    def test_duplicate_email_rejected(self):
        serializer = UserProfileSerializer(
            self.user, data={"email": "erin@example.com"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_same_users_own_email_is_valid(self):
        serializer = UserProfileSerializer(
            self.user, data={"email": "dave@example.com"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class PasswordResetConfirmSerializerTests(TestCase):
    def test_weak_password_rejected(self):
        serializer = PasswordResetConfirmSerializer(
            data={"uidb64": "x", "token": "y", "new_password": "123"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

    def test_strong_password_accepted(self):
        serializer = PasswordResetConfirmSerializer(
            data={"uidb64": "x", "token": "y", "new_password": "AVeryStrongPass987!"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ChangePasswordSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="frank", email="frank@example.com", password="OldPassword123!"
        )
        self.factory = APIRequestFactory()

    def _request_with_user(self):
        django_request = self.factory.post("/fake-url/")
        request = Request(django_request)
        request.user = self.user
        return request

    def test_incorrect_old_password_rejected(self):
        serializer = ChangePasswordSerializer(
            data={"old_password": "WrongPass!", "new_password": "NewStrongPass987!"},
            context={"request": self._request_with_user()},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    def test_correct_old_password_and_strong_new_password_valid(self):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "new_password": "NewStrongPass987!",
            },
            context={"request": self._request_with_user()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------
class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.refresh_url = reverse("token-refresh")
        self.me_url = reverse("me")
        self.password_reset_url = reverse("password-reset")
        self.password_reset_confirm_url = reverse("password-reset-confirm")
        self.change_password_url = reverse("change-password")

        self.user = User.objects.create_user(
            username="gina",
            email="gina@example.com",
            password="OriginalPass123!",
        )

    def _authenticate(self):
        response = self.client.post(
            self.login_url,
            {"username": "gina", "password": "OriginalPass123!"},
        )
        access = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return response.data

    def test_register_creates_user(self):
        payload = {
            "username": "harry",
            "email": "harry@example.com",
            "password": "HarrysPass123!",
        }
        response = self.client.post(self.register_url, payload)
        self.assertIn(
            response.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK)
        )
        self.assertTrue(User.objects.filter(email="harry@example.com").exists())

    def test_login_returns_tokens(self):
        response = self.client.post(
            self.login_url,
            {"username": "gina", "password": "OriginalPass123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_returns_new_access_token(self):
        tokens = self._authenticate()
        response = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_requires_authentication(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_get_returns_profile(self):
        self._authenticate()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "gina@example.com")

    def test_me_patch_updates_allowed_fields(self):
        self._authenticate()
        response = self.client.patch(self.me_url, {"first_name": "Gina"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Gina")

    def test_me_patch_cannot_change_role(self):
        self._authenticate()
        response = self.client.patch(self.me_url, {"role": User.Roles.ADMIN})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Roles.MEMBER)

    def test_me_put_not_allowed(self):
        self._authenticate()
        response = self.client.put(self.me_url, {"first_name": "Gina"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_reset_request_existing_email_sends_mail(self):
        response = self.client.post(
            self.password_reset_url, {"email": "gina@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_request_unknown_email_still_returns_200(self):
        response = self.client.post(
            self.password_reset_url, {"email": "nobody@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_with_valid_token(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)
        response = self.client.post(
            self.password_reset_confirm_url,
            {
                "uidb64": uidb64,
                "token": token,
                "new_password": "BrandNewStrongPass987!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewStrongPass987!"))

    def test_password_reset_confirm_with_invalid_token_fails(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            self.password_reset_confirm_url,
            {
                "uidb64": uidb64,
                "token": "not-a-real-token",
                "new_password": "BrandNewStrongPass987!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_requires_authentication(self):
        response = self.client.post(
            self.change_password_url,
            {"old_password": "x", "new_password": "y"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_success(self):
        self._authenticate()
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "OriginalPass123!",
                "new_password": "AnotherStrongPass987!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherStrongPass987!"))

    def test_change_password_wrong_old_password_fails(self):
        self._authenticate()
        response = self.client.post(
            self.change_password_url,
            {"old_password": "WrongOldPass!", "new_password": "AnotherStrongPass987!"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------
class PermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="StrongPass123!",
            role=User.Roles.ADMIN,
        )
        self.member = User.objects.create_user(
            username="member_user",
            email="member@example.com",
            password="StrongPass123!",
            role=User.Roles.MEMBER,
        )

    def _drf_request(self, method="get", user=None):
        django_request = getattr(self.factory, method)("/fake-url/")
        request = Request(django_request)
        request.user = user
        return request

    def test_is_admin_permission(self):
        perm = IsAdmin()
        self.assertTrue(
            perm.has_permission(self._drf_request(user=self.admin), None)
        )
        self.assertFalse(
            perm.has_permission(self._drf_request(user=self.member), None)
        )

    def test_is_member_permission(self):
        perm = IsMember()
        self.assertTrue(
            perm.has_permission(self._drf_request(user=self.member), None)
        )
        self.assertFalse(
            perm.has_permission(self._drf_request(user=self.admin), None)
        )

    def test_is_admin_or_read_only_allows_reads_for_any_authenticated_user(self):
        perm = IsAdminOrReadOnly()
        self.assertTrue(
            perm.has_permission(self._drf_request(method="get", user=self.member), None)
        )

    def test_is_admin_or_read_only_blocks_writes_for_members(self):
        perm = IsAdminOrReadOnly()
        self.assertFalse(
            perm.has_permission(
                self._drf_request(method="post", user=self.member), None
            )
        )

    def test_is_admin_or_read_only_allows_writes_for_admins(self):
        perm = IsAdminOrReadOnly()
        self.assertTrue(
            perm.has_permission(
                self._drf_request(method="post", user=self.admin), None
            )
        )

    def test_is_owner_or_admin_allows_owner(self):
        perm = IsOwnerOrAdmin()

        class FakeObj:
            user = self.member

        self.assertTrue(
            perm.has_object_permission(
                self._drf_request(user=self.member), None, FakeObj()
            )
        )

    def test_is_owner_or_admin_blocks_non_owner_non_admin(self):
        perm = IsOwnerOrAdmin()

        class FakeObj:
            user = self.admin

        self.assertFalse(
            perm.has_object_permission(
                self._drf_request(user=self.member), None, FakeObj()
            )
        )

    def test_is_owner_or_admin_allows_admin_regardless_of_ownership(self):
        perm = IsOwnerOrAdmin()

        class FakeObj:
            user = self.member

        self.assertTrue(
            perm.has_object_permission(
                self._drf_request(user=self.admin), None, FakeObj()
            )
        )

def test_logout_blacklists_refresh_token(self):
    response = self.client.post(
        self.login_url,
        {
            "username": self.user.username,
            "password": "TestPassword123!",
        },
    )

    refresh = response.data["refresh"]
    access = response.data["access"]

    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = self.client.post(
        self.logout_url,
        {"refresh": refresh},
        format="json",
    )

    self.assertEqual(response.status_code, 200)

    refresh_response = self.client.post(
        self.refresh_url,
        {"refresh": refresh},
        format="json",
    )

    self.assertEqual(refresh_response.status_code, 401)