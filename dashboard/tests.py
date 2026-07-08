from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Author, Book, Genre, Publisher
from fines.models import Fine
from loans.models import Loan
from reservations.models import Reservation
from reviews.models import Review

User = get_user_model()


class DashboardViewsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="password123",
            role=User.Roles.ADMIN,
        )

        self.member = User.objects.create_user(
            username="member",
            email="member@test.com",
            password="password123",
            role=User.Roles.MEMBER,
        )

        self.member2 = User.objects.create_user(
            username="member2",
            email="member2@test.com",
            password="password123",
            role=User.Roles.MEMBER,
        )

        author = Author.objects.create(name="Author")
        genre = Genre.objects.create(name="Fantasy")
        publisher = Publisher.objects.create(name="Publisher")

        self.book1 = Book.objects.create(
            title="Book One",
            isbn="1111111111111",
            publication_year=2022,
            copies=5,
            available_copies=2,
            author=author,
            genre=genre,
            publisher=publisher,
        )

        self.book2 = Book.objects.create(
            title="Book Two",
            isbn="2222222222222",
            publication_year=2023,
            copies=3,
            available_copies=1,
            author=author,
            genre=genre,
            publisher=publisher,
        )

        today = date.today()

        self.loan1 = Loan.objects.create(
            user=self.member,
            book=self.book1,
            due_date=today + timedelta(days=7),
            status=Loan.Status.ACTIVE,
        )

        self.loan2 = Loan.objects.create(
            user=self.member,
            book=self.book1,
            due_date=today - timedelta(days=5),
            status=Loan.Status.OVERDUE,
        )

        self.loan3 = Loan.objects.create(
            user=self.member2,
            book=self.book2,
            due_date=today + timedelta(days=7),
            status=Loan.Status.ACTIVE,
        )

        Reservation.objects.create(
            user=self.member2,
            book=self.book1,
            status=Reservation.Status.PENDING,
        )

        Fine.objects.create(
            loan=self.loan2,
            user=self.member,
            overdue_days=5,
            daily_rate=Decimal("0.50"),
            amount=Decimal("2.50"),
            status=Fine.Status.UNPAID,
        )

        Fine.objects.create(
            loan=self.loan3,
            user=self.member2,
            overdue_days=2,
            daily_rate=Decimal("0.50"),
            amount=Decimal("1.00"),
            status=Fine.Status.PAID,
        )

        Review.objects.create(
            user=self.member,
            book=self.book1,
            rating=5,
        )

        Review.objects.create(
            user=self.member2,
            book=self.book1,
            rating=4,
        )

        Review.objects.create(
            user=self.member,
            book=self.book2,
            rating=3,
        )

        self.client.force_authenticate(self.admin)

    def test_dashboard_statistics(self):
        response = self.client.get(reverse("dashboard-stats"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["total_books"], 2)
        self.assertEqual(response.data["available_books"], 3)
        self.assertEqual(response.data["total_users"], 3)
        self.assertEqual(response.data["total_loans"], 3)
        self.assertEqual(response.data["active_loans"], 2)
        self.assertEqual(response.data["overdue_loans"], 1)
        self.assertEqual(response.data["pending_reservations"], 1)
        self.assertEqual(
            Decimal(response.data["total_fines_collected"]),
            Decimal("1.00"),
        )
        self.assertEqual(
            Decimal(response.data["total_fines_outstanding"]),
            Decimal("2.50"),
        )

    def test_popular_books_report(self):
        response = self.client.get(reverse("popular-books"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        books = response.data["results"]

        self.assertEqual(len(books), 2)

        self.assertEqual(books[0]["title"], "Book One")
        self.assertAlmostEqual(books[0]["average_rating"], 4.5)
        self.assertEqual(books[0]["review_count"], 2)

    def test_most_borrowed_books_report(self):
        response = self.client.get(reverse("most-borrowed-books"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        books = response.data["results"]

        self.assertEqual(books[0]["title"], "Book One")
        self.assertEqual(books[0]["loan_count"], 2)

    def test_most_active_users_report(self):
        response = self.client.get(reverse("most-active-users"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users = response.data["results"]

        self.assertEqual(users[0]["username"], "member")
        self.assertEqual(users[0]["loan_count"], 2)

    def test_overdue_users_report(self):
        response = self.client.get(reverse("overdue-users"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users = response.data["results"]

        self.assertEqual(len(users), 1)

        self.assertEqual(users[0]["username"], "member")
        self.assertEqual(users[0]["overdue_loans"], 1)
        self.assertEqual(
            Decimal(users[0]["outstanding_fines"]),
            Decimal("2.50"),
        )

    def test_monthly_borrowing_report(self):
        response = self.client.get(reverse("monthly-borrowing"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

        self.assertIn("month", response.data[0])
        self.assertIn("count", response.data[0])

    def test_member_cannot_access_dashboard(self):
        self.client.force_authenticate(self.member)

        response = self.client.get(reverse("dashboard-stats"))

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_cannot_access_dashboard(self):
        self.client.force_authenticate(None)

        response = self.client.get(reverse("dashboard-stats"))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )