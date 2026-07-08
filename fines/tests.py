"""
fines/tests.py

Covers:
  - Model tests
  - Service tests (both entry points, idempotent notification, settled
    fines aren't recalculated, no-fine-if-not-overdue)
  - Management command test (calculate_fines)
  - API tests (list scoping, retrieve, pay/waive permissions and state
    transitions)
  - Integration test confirming LoanService.return_book() actually
    finalizes a fine on a late return
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Author, Book, Genre, Publisher
from loans.models import Loan
from loans.services import LoanService

from .models import Fine
from .services import FineService

User = get_user_model()


def make_book(**overrides):
    author, _ = Author.objects.get_or_create(
        name=overrides.pop("author_name", "Test Author")
    )
    genre, _ = Genre.objects.get_or_create(
        name=overrides.pop("genre_name", "Test Genre")
    )
    publisher, _ = Publisher.objects.get_or_create(
        name=overrides.pop("publisher_name", "Test Publisher")
    )
    defaults = dict(
        title="Dune",
        isbn=overrides.pop("isbn", "9780441013593"),
        publication_year=1965,
        copies=1,
        available_copies=1,
        author=author,
        genre=genre,
        publisher=publisher,
    )
    defaults.update(overrides)
    return Book.objects.create(**defaults)


@override_settings(DAILY_FINE_AMOUNT="1.00")
class FineModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="StrongPass123!"
        )
        self.book = make_book(available_copies=0)
        self.loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
        )

    def test_default_status_is_unpaid(self):
        fine = Fine.objects.create(
            loan=self.loan,
            user=self.user,
            overdue_days=3,
            daily_rate=Decimal("1.00"),
            amount=Decimal("3.00"),
        )
        self.assertEqual(fine.status, Fine.Status.UNPAID)

    def test_str_representation(self):
        fine = Fine.objects.create(
            loan=self.loan,
            user=self.user,
            overdue_days=3,
            daily_rate=Decimal("1.00"),
            amount=Decimal("3.00"),
        )
        self.assertIn(str(fine.amount), str(fine))

    def test_one_fine_per_loan_enforced(self):
        Fine.objects.create(
            loan=self.loan,
            user=self.user,
            overdue_days=3,
            daily_rate=Decimal("1.00"),
            amount=Decimal("3.00"),
        )
        with self.assertRaises(Exception):
            Fine.objects.create(
                loan=self.loan,
                user=self.user,
                overdue_days=5,
                daily_rate=Decimal("1.00"),
                amount=Decimal("5.00"),
            )


@override_settings(DAILY_FINE_AMOUNT="1.00")
class FineServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="StrongPass123!"
        )
        self.book = make_book(available_copies=0)

    def test_recalculate_creates_fine_for_overdue_active_loan(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=4),
        )
        fine = FineService.recalculate_fine_for_active_loan(loan)
        self.assertIsNotNone(fine)
        self.assertEqual(fine.overdue_days, 4)
        self.assertEqual(fine.amount, Decimal("4.00"))

    def test_recalculate_returns_none_when_not_overdue(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=2),
        )
        fine = FineService.recalculate_fine_for_active_loan(loan)
        self.assertIsNone(fine)
        self.assertFalse(Fine.objects.filter(loan=loan).exists())

    def test_recalculate_updates_existing_unpaid_fine(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=2),
        )
        first = FineService.recalculate_fine_for_active_loan(loan)
        self.assertEqual(first.overdue_days, 2)

        # Simulate another day passing by re-running against a later date
        # via a fresh due_date-derived overdue window.
        loan.due_date = timezone.localdate() - timedelta(days=5)
        loan.save(update_fields=["due_date"])
        second = FineService.recalculate_fine_for_active_loan(loan)

        self.assertEqual(first.pk, second.pk)  # same row, updated in place
        self.assertEqual(second.overdue_days, 5)
        self.assertEqual(second.amount, Decimal("5.00"))

    def test_recalculate_does_not_touch_paid_fine(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=2),
        )
        fine = FineService.recalculate_fine_for_active_loan(loan)
        FineService.mark_paid(fine)

        loan.due_date = timezone.localdate() - timedelta(days=10)
        loan.save(update_fields=["due_date"])
        result = FineService.recalculate_fine_for_active_loan(loan)

        fine.refresh_from_db()
        self.assertEqual(result.pk, fine.pk)
        self.assertEqual(fine.overdue_days, 2)  # unchanged, still settled
        self.assertEqual(fine.status, Fine.Status.PAID)

    def test_finalize_on_return_uses_returned_at_date(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=6),
        )
        loan.status = Loan.Status.RETURNED
        loan.returned_at = timezone.now() - timedelta(days=1)  # returned 1 day ago
        loan.save(update_fields=["status", "returned_at"])

        fine = FineService.finalize_fine_on_return(loan)
        expected_days = (loan.returned_at.date() - loan.due_date).days
        self.assertEqual(fine.overdue_days, expected_days)

    def test_notify_fine_issued_called_once_on_creation(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        from notifications.models import Notification

        FineService.recalculate_fine_for_active_loan(loan)
        FineService.recalculate_fine_for_active_loan(loan)  # called again

        count = Notification.objects.filter(
            loan=loan, notification_type=Notification.NotificationType.FINE_ISSUED
        ).count()
        self.assertEqual(count, 1)

    def test_mark_paid_sets_status_and_timestamp(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        fine = FineService.recalculate_fine_for_active_loan(loan)
        FineService.mark_paid(fine)
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.Status.PAID)
        self.assertIsNotNone(fine.paid_at)

    def test_waive_sets_status_and_timestamp(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        fine = FineService.recalculate_fine_for_active_loan(loan)
        FineService.waive(fine)
        fine.refresh_from_db()
        self.assertEqual(fine.status, Fine.Status.WAIVED)
        self.assertIsNotNone(fine.waived_at)


@override_settings(DAILY_FINE_AMOUNT="1.00")
class CalculateFinesCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="StrongPass123!"
        )
        self.book = make_book(available_copies=0)

    def test_command_transitions_active_loan_to_overdue_and_creates_fine(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
        )
        call_command("calculate_fines")

        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.OVERDUE)
        self.assertTrue(Fine.objects.filter(loan=loan).exists())

    def test_command_ignores_loans_not_yet_due(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=3),
        )
        call_command("calculate_fines")

        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.ACTIVE)
        self.assertFalse(Fine.objects.filter(loan=loan).exists())

    def test_command_is_safe_to_run_twice(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=2),
        )
        call_command("calculate_fines")
        call_command("calculate_fines")

        self.assertEqual(Fine.objects.filter(loan=loan).count(), 1)


@override_settings(DAILY_FINE_AMOUNT="1.00")
class LoanReturnFinalizesFineIntegrationTests(TestCase):
    """Confirms the hook added to LoanService.return_book() actually works."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="StrongPass123!"
        )
        self.book = make_book(available_copies=0)

    def test_returning_a_late_loan_creates_a_fine(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=4),
        )
        LoanService.return_book(loan=loan)

        self.assertTrue(Fine.objects.filter(loan=loan).exists())
        fine = Fine.objects.get(loan=loan)
        self.assertEqual(fine.overdue_days, 4)

    def test_returning_an_on_time_loan_creates_no_fine(self):
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=2),
        )
        LoanService.return_book(loan=loan)
        self.assertFalse(Fine.objects.filter(loan=loan).exists())

    def test_returning_an_overdue_status_loan_succeeds(self):
        """
        Regression test for the return_book() status-guard fix: a loan
        already transitioned to OVERDUE by calculate_fines must still be
        returnable.
        """
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        call_command("calculate_fines")
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.OVERDUE)

        returned_loan = LoanService.return_book(loan=loan)
        self.assertEqual(returned_loan.status, Loan.Status.RETURNED)


@override_settings(DAILY_FINE_AMOUNT="1.00")
class FineAPITests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="member1", email="member1@example.com", password="StrongPass123!"
        )
        self.other_member = User.objects.create_user(
            username="member2", email="member2@example.com", password="StrongPass123!"
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="StrongPass123!",
            role=User.Roles.ADMIN,
        )

        self.book = make_book(available_copies=0)

        self.own_loan = Loan.objects.create(
            user=self.member,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
        )
        self.own_fine = FineService.recalculate_fine_for_active_loan(self.own_loan)

        self.other_book = make_book(
            isbn="9780553293357", title="Foundation", available_copies=0
        )
        self.other_loan = Loan.objects.create(
            user=self.other_member,
            book=self.other_book,
            due_date=timezone.localdate() - timedelta(days=2),
        )
        self.other_fine = FineService.recalculate_fine_for_active_loan(self.other_loan)

    def _login(self, user, password="StrongPass123!"):
        response = self.client.post(
            "/api/v1/auth/login/", {"username": user.username, "password": password}
        )
        access = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_member_sees_only_own_fines(self):
        self._login(self.member)
        response = self.client.get("/api/v1/fines/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data.get("results", response.data)]
        self.assertIn(self.own_fine.id, ids)
        self.assertNotIn(self.other_fine.id, ids)

    def test_admin_sees_all_fines(self):
        self._login(self.admin)
        response = self.client.get("/api/v1/fines/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data.get("results", response.data)]
        self.assertIn(self.own_fine.id, ids)
        self.assertIn(self.other_fine.id, ids)

    def test_member_cannot_retrieve_others_fine(self):
        self._login(self.member)
        response = self.client.get(f"/api/v1/fines/{self.other_fine.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_pay_fine(self):
        self._login(self.member)
        response = self.client.post(f"/api/v1/fines/{self.own_fine.id}/pay/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_pay_fine(self):
        self._login(self.admin)
        response = self.client.post(f"/api/v1/fines/{self.own_fine.id}/pay/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.own_fine.refresh_from_db()
        self.assertEqual(self.own_fine.status, Fine.Status.PAID)

    def test_admin_can_waive_fine(self):
        self._login(self.admin)
        response = self.client.post(f"/api/v1/fines/{self.own_fine.id}/waive/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.own_fine.refresh_from_db()
        self.assertEqual(self.own_fine.status, Fine.Status.WAIVED)

    def test_cannot_pay_already_paid_fine(self):
        self._login(self.admin)
        self.client.post(f"/api/v1/fines/{self.own_fine.id}/pay/")
        response = self.client.post(f"/api/v1/fines/{self.own_fine.id}/pay/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)