from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from books.models import Author, Book, Genre, Publisher

from .models import Reservation


class ReservationAPITestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="StrongPass123!",
            role=User.Roles.ADMIN,
        )
        self.member_a = User.objects.create_user(
            username="member_a",
            email="member_a@example.com",
            password="StrongPass123!",
            role=User.Roles.MEMBER,
        )
        self.member_b = User.objects.create_user(
            username="member_b",
            email="member_b@example.com",
            password="StrongPass123!",
            role=User.Roles.MEMBER,
        )

        self.author = Author.objects.create(name="Jane Doe")
        self.genre = Genre.objects.create(name="Fiction")
        self.publisher = Publisher.objects.create(
            name="Acme Publishing", email="acme@example.com"
        )

        self.unavailable_book = Book.objects.create(
            title="Rare Book",
            isbn="1111111111111",
            publication_year=2020,
            copies=1,
            available_copies=0,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )
        self.available_book = Book.objects.create(
            title="Common Book",
            isbn="2222222222222",
            publication_year=2020,
            copies=5,
            available_copies=5,
            author=self.author,
            genre=self.genre,
            publisher=self.publisher,
        )

        self.list_create_url = reverse("reservation-list")

    def _cancel_url(self, reservation_id):
        return reverse("reservation-cancel", kwargs={"pk": reservation_id})

    def test_member_can_reserve_unavailable_book(self):
        self.client.force_authenticate(self.member_a)
        response = self.client.post(
            self.list_create_url, {"book": self.unavailable_book.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Reservation.Status.PENDING)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_cannot_reserve_available_book(self):
        self.client.force_authenticate(self.member_a)
        response = self.client.post(
            self.list_create_url, {"book": self.available_book.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_cannot_create_duplicate_pending_reservation(self):
        self.client.force_authenticate(self.member_a)
        self.client.post(self.list_create_url, {"book": self.unavailable_book.id})
        response = self.client.post(
            self.list_create_url, {"book": self.unavailable_book.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_member_cannot_view_other_member_reservations(self):
        reservation = Reservation.objects.create(
            user=self.member_a, book=self.unavailable_book
        )
        self.client.force_authenticate(self.member_b)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data["results"]] \
            if "results" in response.data else [item["id"] for item in response.data]
        self.assertNotIn(reservation.id, returned_ids)

    def test_admin_can_view_all_reservations(self):
        Reservation.objects.create(user=self.member_a, book=self.unavailable_book)
        Reservation.objects.create(user=self.member_b, book=self.available_book)
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        count = response.data["count"] if "count" in response.data else len(response.data)
        self.assertEqual(count, 2)

    def test_member_can_cancel_own_reservation(self):
        reservation = Reservation.objects.create(
            user=self.member_a, book=self.unavailable_book
        )
        self.client.force_authenticate(self.member_a)
        response = self.client.post(self._cancel_url(reservation.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)

    def test_member_cannot_cancel_other_member_reservation(self):
        reservation = Reservation.objects.create(
            user=self.member_a, book=self.unavailable_book
        )
        self.client.force_authenticate(self.member_b)
        response = self.client.post(self._cancel_url(reservation.id))
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.PENDING)

    def test_cannot_cancel_already_cancelled_reservation(self):
        reservation = Reservation.objects.create(
            user=self.member_a,
            book=self.unavailable_book,
            status=Reservation.Status.CANCELLED,
        )
        self.client.force_authenticate(self.member_a)
        response = self.client.post(self._cancel_url(reservation.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
