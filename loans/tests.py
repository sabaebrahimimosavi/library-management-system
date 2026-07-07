from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import (
    Author,
    Genre,
    Publisher,
    Book,
)

from loans.models import Loan

User = get_user_model()


class LoanAPITests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123456",
            role="ADMIN",
        )

        self.member = User.objects.create_user(
            username="member",
            email="member@test.com",
            password="member123456",
            role="MEMBER",
        )

        self.member2 = User.objects.create_user(
            username="member2",
            email="member2@test.com",
            password="member123456",
            role="MEMBER",
        )

        self.author = Author.objects.create(
            name="George Orwell"
        )

        self.genre = Genre.objects.create(
            name="Science Fiction"
        )

        self.publisher = Publisher.objects.create(
            name="Penguin"
        )

        self.book = Book.objects.create(
            title="1984",
            isbn="9780451524935",
            publication_year=1949,
            copies=5,
            available_copies=5,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )

        self.borrow_url = "/api/v1/loans/"

    def test_member_can_borrow_book(self):
        self.client.force_authenticate(self.member)

        response = self.client.post(
            self.borrow_url,
            {
                "book": self.book.id,
                "due_date": date.today() + timedelta(days=14),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Loan.objects.count(),
            1,
        )

    def test_available_copies_decreases_on_borrow(self):
        self.client.force_authenticate(self.member)

        self.client.post(
            self.borrow_url,
            {
                "book": self.book.id,
                "due_date": date.today() + timedelta(days=14),
            },
            format="json",
        )

        self.book.refresh_from_db()

        self.assertEqual(
            self.book.available_copies,
            4,
        )

    def test_cannot_borrow_unavailable_book(self):
        self.book.available_copies = 0
        self.book.save()

        self.client.force_authenticate(self.member)

        response = self.client.post(
            self.borrow_url,
            {
                "book": self.book.id,
                "due_date": date.today() + timedelta(days=14),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.data["detail"],
            "Book is not available.",
        )

    def test_return_book(self):
        loan = Loan.objects.create(
            user=self.member,
            book=self.book,
            due_date=date.today() + timedelta(days=14),
        )

        self.book.available_copies -= 1
        self.book.save()

        self.client.force_authenticate(self.member)

        response = self.client.post(
            f"/api/v1/loans/{loan.id}/return_book/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        loan.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            loan.user,
            self.member,
        )

        self.assertEqual(
            loan.book,
            self.book,
        )

        self.assertEqual(
            loan.status,
            Loan.Status.RETURNED,
        )

        self.assertIsNotNone(
            loan.returned_at,
        )

        self.assertEqual(
            self.book.available_copies,
            5,
        )

    def test_member_cannot_view_other_member_loans(self):
        Loan.objects.create(
            user=self.member,
            book=self.book,
            due_date=date.today() + timedelta(days=14),
        )

        Loan.objects.create(
            user=self.member2,
            book=self.book,
            due_date=date.today() + timedelta(days=14),
        )

        self.client.force_authenticate(self.member)

        response = self.client.get(
            "/api/v1/loans/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["user"],
            self.member.id,
        )

    def test_admin_can_view_all_loans(self):
        Loan.objects.create(
            user=self.member,
            book=self.book,
            due_date=date.today() + timedelta(days=14),
        )

        Loan.objects.create(
            user=self.member2,
            book=self.book,
            due_date=date.today() + timedelta(days=14),
        )

        self.client.force_authenticate(self.admin)

        response = self.client.get(
            "/api/v1/loans/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )