# from datetime import date, timedelta

# from django.contrib.auth import get_user_model
# from rest_framework import status
# from rest_framework.test import APITestCase

# from books.models import (
#     Author,
#     Genre,
#     Publisher,
#     Book,
# )

# from loans.models import Loan

# User = get_user_model()


# class LoanAPITests(APITestCase):

#     def setUp(self):
#         self.admin = User.objects.create_user(
#             username="admin",
#             email="admin@test.com",
#             password="admin123456",
#             role="ADMIN",
#         )

#         self.member = User.objects.create_user(
#             username="member",
#             email="member@test.com",
#             password="member123456",
#             role="MEMBER",
#         )

#         self.member2 = User.objects.create_user(
#             username="member2",
#             email="member2@test.com",
#             password="member123456",
#             role="MEMBER",
#         )

#         self.author = Author.objects.create(
#             name="George Orwell"
#         )

#         self.genre = Genre.objects.create(
#             name="Science Fiction"
#         )

#         self.publisher = Publisher.objects.create(
#             name="Penguin"
#         )

#         self.book = Book.objects.create(
#             title="1984",
#             isbn="9780451524935",
#             publication_year=1949,
#             copies=5,
#             available_copies=5,
#             author=self.author,
#             genre=self.genre,
#             publisher=self.publisher,
#         )

#         self.borrow_url = "/api/v1/loans/"

#     def test_member_can_borrow_book(self):
#         self.client.force_authenticate(self.member)

#         response = self.client.post(
#             self.borrow_url,
#             {
#                 "book": self.book.id,
#                 "due_date": date.today() + timedelta(days=14),
#             },
#             format="json",
#         )

#         self.assertEqual(
#             response.status_code,
#             status.HTTP_201_CREATED,
#         )

#         self.assertEqual(
#             Loan.objects.count(),
#             1,
#         )

#     def test_available_copies_decreases_on_borrow(self):
#         self.client.force_authenticate(self.member)

#         self.client.post(
#             self.borrow_url,
#             {
#                 "book": self.book.id,
#                 "due_date": date.today() + timedelta(days=14),
#             },
#             format="json",
#         )

#         self.book.refresh_from_db()

#         self.assertEqual(
#             self.book.available_copies,
#             4,
#         )

#     def test_cannot_borrow_unavailable_book(self):
#         self.book.available_copies = 0
#         self.book.save()

#         self.client.force_authenticate(self.member)

#         response = self.client.post(
#             self.borrow_url,
#             {
#                 "book": self.book.id,
#                 "due_date": date.today() + timedelta(days=14),
#             },
#             format="json",
#         )

#         self.assertEqual(
#             response.status_code,
#             status.HTTP_400_BAD_REQUEST,
#         )
#         self.assertEqual(
#             response.data["detail"],
#             "Book is not available.",
#         )

#     def test_return_book(self):
#         loan = Loan.objects.create(
#             user=self.member,
#             book=self.book,
#             due_date=date.today() + timedelta(days=14),
#         )

#         self.book.available_copies -= 1
#         self.book.save()

#         self.client.force_authenticate(self.member)

#         response = self.client.post(
#             f"/api/v1/loans/{loan.id}/return_book/"
#         )

#         self.assertEqual(
#             response.status_code,
#             status.HTTP_200_OK,
#         )

#         loan.refresh_from_db()
#         self.book.refresh_from_db()

#         self.assertEqual(
#             loan.user,
#             self.member,
#         )

#         self.assertEqual(
#             loan.book,
#             self.book,
#         )

#         self.assertEqual(
#             loan.status,
#             Loan.Status.RETURNED,
#         )

#         self.assertIsNotNone(
#             loan.returned_at,
#         )

#         self.assertEqual(
#             self.book.available_copies,
#             5,
#         )

#     def test_member_cannot_view_other_member_loans(self):
#         Loan.objects.create(
#             user=self.member,
#             book=self.book,
#             due_date=date.today() + timedelta(days=14),
#         )

#         Loan.objects.create(
#             user=self.member2,
#             book=self.book,
#             due_date=date.today() + timedelta(days=14),
#         )

#         self.client.force_authenticate(self.member)

#         response = self.client.get(
#             "/api/v1/loans/"
#         )

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["count"], 1)
#         self.assertEqual(len(response.data["results"]), 1)
#         self.assertEqual(
#             response.data["results"][0]["user"],
#             self.member.id,
#         )

#     def test_admin_can_view_all_loans(self):
#         Loan.objects.create(
#             user=self.member,
#             book=self.book,
#             due_date=date.today() + timedelta(days=14),
#         )

#         Loan.objects.create(
#             user=self.member2,
#             book=self.book,
#             due_date=date.today() + timedelta(days=14),
#         )

#         self.client.force_authenticate(self.admin)

#         response = self.client.get(
#             "/api/v1/loans/"
#         )

#         self.assertEqual(
#             response.status_code,
#             status.HTTP_200_OK,
#         )

#         self.assertEqual(
#             response.data["count"],
#             2,
#         )

#         self.assertEqual(
#             len(response.data["results"]),
#             2,
#         )

"""
loans/tests.py — ADD this class (or merge into your existing loans test
file) to cover the Phase 5 changes to LoanService: notifying every pending
reservation on return, and fulfilling the borrower's own reservation on
borrow.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from books.models import Author, Book, Genre, Publisher
from notifications.services import NotificationService
from reservations.models import Reservation
from reservations.services import ReservationService

from .models import Loan
from .services import LoanService

User = get_user_model()


class LoanServiceReservationIntegrationTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Frank Herbert")
        self.genre = Genre.objects.create(name="Science Fiction")
        self.publisher = Publisher.objects.create(name="Ace Books")

        self.book = Book.objects.create(
            title="Dune",
            isbn="9780441013593",
            publication_year=1965,
            copies=1,
            available_copies=0,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )

        self.first_reserver = User.objects.create_user(
            username="first_reserver",
            email="first@example.com",
            password="StrongPass123!",
        )
        self.second_reserver = User.objects.create_user(
            username="second_reserver",
            email="second@example.com",
            password="StrongPass123!",
        )
        self.borrower = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="StrongPass123!"
        )

        # Two members waiting in the queue, oldest first.
        self.reservation_1 = Reservation.objects.create(
            user=self.first_reserver, book=self.book, status=Reservation.Status.PENDING
        )
        self.reservation_2 = Reservation.objects.create(
            user=self.second_reserver, book=self.book, status=Reservation.Status.PENDING
        )

        # A loan on the book so there's something to return.
        self.active_loan = Loan.objects.create(
            user=self.borrower,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=7),
        )

    def test_return_book_notifies_every_pending_reservation_not_just_the_first(self):
        with patch.object(
            NotificationService, "notify_reservation_available"
        ) as mock_notify:
            LoanService.return_book(loan=self.active_loan)

        notified_reservations = {call.args[0] for call in mock_notify.call_args_list}
        self.assertEqual(mock_notify.call_count, 2)
        self.assertIn(self.reservation_1, notified_reservations)
        self.assertIn(self.reservation_2, notified_reservations)

    def test_return_book_increments_available_copies(self):
        LoanService.return_book(loan=self.active_loan)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

    def test_return_book_with_no_reservations_sends_no_notifications(self):
        self.reservation_1.delete()
        self.reservation_2.delete()
        with patch.object(
            NotificationService, "notify_reservation_available"
        ) as mock_notify:
            LoanService.return_book(loan=self.active_loan)
        mock_notify.assert_not_called()

    def test_borrow_book_by_reserving_user_marks_their_reservation_fulfilled(self):
        # Free up a copy first (as return_book would).
        self.book.available_copies = 1
        self.book.save(update_fields=["available_copies"])

        LoanService.borrow_book(
            user=self.first_reserver,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=14),
        )

        self.reservation_1.refresh_from_db()
        self.assertEqual(self.reservation_1.status, Reservation.Status.FULFILLED)

        # The other member's reservation is untouched — still waiting.
        self.reservation_2.refresh_from_db()
        self.assertEqual(self.reservation_2.status, Reservation.Status.PENDING)

    def test_borrow_book_by_non_reserving_user_does_not_touch_queue(self):
        self.book.available_copies = 1
        self.book.save(update_fields=["available_copies"])

        walk_in_user = User.objects.create_user(
            username="walk_in", email="walkin@example.com", password="StrongPass123!"
        )
        LoanService.borrow_book(
            user=walk_in_user,
            book=self.book,
            due_date=timezone.localdate() + timedelta(days=14),
        )

        self.reservation_1.refresh_from_db()
        self.reservation_2.refresh_from_db()
        self.assertEqual(self.reservation_1.status, Reservation.Status.PENDING)
        self.assertEqual(self.reservation_2.status, Reservation.Status.PENDING)

    def test_borrow_book_raises_when_no_copies_available(self):
        self.book.available_copies = 0
        self.book.save(update_fields=["available_copies"])
        with self.assertRaises(ValueError):
            LoanService.borrow_book(
                user=self.borrower,
                book=self.book,
                due_date=timezone.localdate() + timedelta(days=14),
            )


class ReservationServiceQueryMethodTests(TestCase):
    """Covers the two new lookup methods added to ReservationService."""

    def setUp(self):
        self.author = Author.objects.create(name="Isaac Asimov")
        self.genre = Genre.objects.create(name="Science Fiction Classics")
        self.publisher = Publisher.objects.create(name="Gnome Press")

        self.book = Book.objects.create(
            title="Foundation",
            isbn="9780553293357",
            publication_year=1951,
            copies=1,
            available_copies=0,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )
        self.other_book = Book.objects.create(
            title="Other Book",
            isbn="9780000000001",
            publication_year=2000,
            copies=1,
            available_copies=1,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )

        self.user_a = User.objects.create_user(
            username="user_a", email="a@example.com", password="StrongPass123!"
        )
        self.user_b = User.objects.create_user(
            username="user_b", email="b@example.com", password="StrongPass123!"
        )

        self.reservation_a = Reservation.objects.create(
            user=self.user_a, book=self.book, status=Reservation.Status.PENDING
        )
        self.reservation_b = Reservation.objects.create(
            user=self.user_b, book=self.book, status=Reservation.Status.PENDING
        )
        self.cancelled_reservation = Reservation.objects.create(
            user=self.user_a, book=self.other_book, status=Reservation.Status.CANCELLED
        )

    def test_get_pending_reservations_returns_only_pending_for_that_book(self):
        results = list(ReservationService.get_pending_reservations(book=self.book))
        self.assertEqual(len(results), 2)
        self.assertIn(self.reservation_a, results)
        self.assertIn(self.reservation_b, results)

    def test_get_pending_reservations_ordered_oldest_first(self):
        results = list(ReservationService.get_pending_reservations(book=self.book))
        self.assertEqual(results[0].reserved_at, min(r.reserved_at for r in results))

    def test_get_pending_reservation_for_user_returns_correct_reservation(self):
        result = ReservationService.get_pending_reservation_for_user(
            book=self.book, user=self.user_a
        )
        self.assertEqual(result, self.reservation_a)

    def test_get_pending_reservation_for_user_returns_none_when_absent(self):
        result = ReservationService.get_pending_reservation_for_user(
            book=self.other_book, user=self.user_b
        )
        self.assertIsNone(result)

    def test_get_pending_reservation_for_user_ignores_cancelled(self):
        result = ReservationService.get_pending_reservation_for_user(
            book=self.other_book, user=self.user_a
        )
        self.assertIsNone(result)