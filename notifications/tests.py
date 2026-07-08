from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Author, Genre, Publisher, Book
from loans.models import Loan
from reservations.models import Reservation

from .models import Notification
from .services import (
    NotificationService,
    NotificationChannelService,
)

User = get_user_model()


# ============================================================
# Helpers
# ============================================================

def create_book(
    title="Dune",
    isbn="9780441013593",
    available_copies=5,
):
    author = Author.objects.create(
        name=f"Author {isbn}"
    )

    genre = Genre.objects.create(
        name=f"Genre {isbn}"
    )

    publisher = Publisher.objects.create(
        name=f"Publisher {isbn}"
    )

    return Book.objects.create(
        title=title,
        isbn=isbn,
        publication_year=1965,
        copies=5,
        available_copies=available_copies,
        author=author,
        genre=genre,
        publisher=publisher,
    )


# ============================================================
# Model Tests
# ============================================================

class NotificationModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="StrongPass123!"
        )

    def test_default_status_is_pending(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.DUE_SOON_REMINDER,
            message="test"
        )

        self.assertEqual(
            notification.status,
            Notification.Status.PENDING
        )

        self.assertFalse(notification.is_read)

    def test_string_representation(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.DUE_TODAY_REMINDER,
            message="test"
        )

        self.assertIn(
            self.user.username,
            str(notification)
        )


# ============================================================
# Due Date Service Tests
# ============================================================

class NotificationServiceDueDateTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="borrower",
            email="borrower@example.com",
            password="StrongPass123!"
        )

        self.book = create_book()

        self.loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=2),
        )

    def test_notify_due_soon_sends_email(self):
        notification = NotificationService.notify_due_soon(
            self.loan
        )

        self.assertIsNotNone(notification)

        self.assertEqual(
            notification.status,
            Notification.Status.SENT
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            "due in 2 days",
            mail.outbox[0].subject.lower()
        )

    def test_notify_due_soon_is_idempotent(self):
        first = NotificationService.notify_due_soon(
            self.loan
        )

        second = NotificationService.notify_due_soon(
            self.loan
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

        self.assertEqual(len(mail.outbox), 1)

    def test_notify_due_today_sends_email(self):
        self.loan.due_date = timezone.localdate()
        self.loan.save()

        notification = NotificationService.notify_due_today(
            self.loan
        )

        self.assertIsNotNone(notification)

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            "due today",
            mail.outbox[0].subject.lower()
        )

    def test_due_soon_and_due_today_are_independent(self):
        NotificationService.notify_due_soon(
            self.loan
        )

        self.loan.due_date = timezone.localdate()
        self.loan.save()

        NotificationService.notify_due_today(
            self.loan
        )

        self.assertEqual(
            Notification.objects.count(),
            2
        )

    def test_failed_delivery_marks_notification_failed(self):
        with patch.object(
            NotificationChannelService,
            "send_email",
            side_effect=Exception("boom")
        ):
            notification = (
                NotificationService.notify_due_soon(
                    self.loan
                )
            )

        self.assertEqual(
            notification.status,
            Notification.Status.FAILED
        )

        self.assertIn(
            "boom",
            notification.failure_reason
        )


# ============================================================
# Reservation Service Tests
# ============================================================

class NotificationServiceReservationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="waiting_member",
            email="waiting@example.com",
            password="StrongPass123!"
        )

        self.book = create_book(
            title="1984",
            isbn="9780451524935",
            available_copies=0,
        )

        self.reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
        )

    def test_notify_reservation_available_sends_email(self):
        notification = (
            NotificationService.notify_reservation_available(
                self.reservation
            )
        )

        self.assertIsNotNone(notification)

        self.assertEqual(
            len(mail.outbox),
            1
        )

        self.assertIn(
            "available",
            mail.outbox[0].subject.lower()
        )

    def test_notify_reservation_available_is_idempotent(self):
        first = (
            NotificationService.notify_reservation_available(
                self.reservation
            )
        )

        second = (
            NotificationService.notify_reservation_available(
                self.reservation
            )
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

        self.assertEqual(
            len(mail.outbox),
            1
        )


# ============================================================
# API Tests
# ============================================================

class NotificationAPITests(APITestCase):

    def setUp(self):
        self.member = User.objects.create_user(
            username="member1",
            email="member1@example.com",
            password="StrongPass123!"
        )

        self.other_member = User.objects.create_user(
            username="member2",
            email="member2@example.com",
            password="StrongPass123!"
        )

        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="StrongPass123!",
            role=User.Roles.ADMIN,
        )

        self.own_notification = Notification.objects.create(
            user=self.member,
            notification_type=(
                Notification.NotificationType.DUE_SOON_REMINDER
            ),
            message="due soon"
        )

        self.other_notification = Notification.objects.create(
            user=self.other_member,
            notification_type=(
                Notification.NotificationType.RESERVATION_AVAILABLE
            ),
            message="available"
        )

    def login(self, user):
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": user.username,
                "password": "StrongPass123!",
            }
        )

        token = response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def test_member_sees_only_own_notifications(self):
        self.login(self.member)

        response = self.client.get(
            "/api/v1/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.own_notification.id,
            ids
        )

        self.assertNotIn(
            self.other_notification.id,
            ids
        )

    def test_admin_sees_all_notifications(self):
        self.login(self.admin)

        response = self.client.get(
            "/api/v1/notifications/"
        )

        ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.own_notification.id,
            ids
        )

        self.assertIn(
            self.other_notification.id,
            ids
        )

    def test_member_cannot_retrieve_other_notification(self):
        self.login(self.member)

        response = self.client.get(
            f"/api/v1/notifications/{self.other_notification.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_member_can_mark_read(self):
        self.login(self.member)

        response = self.client.post(
            f"/api/v1/notifications/{self.own_notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.own_notification.refresh_from_db()

        self.assertTrue(
            self.own_notification.is_read
        )

    def test_member_cannot_mark_other_notification_read(self):
        self.login(self.member)

        response = self.client.post(
            f"/api/v1/notifications/{self.other_notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )