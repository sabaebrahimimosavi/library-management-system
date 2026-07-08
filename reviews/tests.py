"""
reviews/tests.py

Covers:
  - Model tests (str, uniqueness constraint, rating range validation)
  - Service tests (create success, duplicate rejected, loan-history
    requirement enforced and toggleable via settings, update-in-place)
  - API tests (nested list/create under a book, retrieve/update/delete
    permissions, average_rating/review_count on the book detail endpoint)
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APITestCase

from books.models import Author, Book, Genre, Publisher
from loans.models import Loan

from .models import Review
from .services import ReviewService

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
        copies=2,
        available_copies=2,
        author=author,
        genre=genre,
        publisher=publisher,
    )
    defaults.update(overrides)
    return Book.objects.create(**defaults)


# ---------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------
class ReviewModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reader", email="reader@example.com", password="StrongPass123!"
        )
        self.book = make_book()

    def test_str_representation(self):
        review = Review.objects.create(user=self.user, book=self.book, rating=4)
        self.assertIn("4/5", str(review))

    def test_one_review_per_user_book_enforced(self):
        Review.objects.create(user=self.user, book=self.book, rating=5)
        with self.assertRaises(IntegrityError):
            Review.objects.create(user=self.user, book=self.book, rating=3)

    def test_rating_above_five_rejected_on_full_clean(self):
        review = Review(user=self.user, book=self.book, rating=6)
        with self.assertRaises(DjangoValidationError):
            review.full_clean()

    def test_rating_below_one_rejected_on_full_clean(self):
        review = Review(user=self.user, book=self.book, rating=0)
        with self.assertRaises(DjangoValidationError):
            review.full_clean()


# ---------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------
class ReviewServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reader2", email="reader2@example.com", password="StrongPass123!"
        )
        self.book = make_book(isbn="9780000000011")

    def test_create_review_requires_loan_history_by_default(self):
        with self.assertRaises(DRFValidationError):
            ReviewService.create_review(user=self.user, book=self.book, rating=5)
        self.assertFalse(Review.objects.filter(user=self.user, book=self.book).exists())

    def test_create_review_succeeds_after_borrowing(self):
        Loan.objects.create(user=self.user, book=self.book, due_date="2099-01-01")
        review = ReviewService.create_review(
            user=self.user, book=self.book, rating=5, comment="Great read"
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great read")

    @override_settings(REVIEWS_REQUIRE_LOAN_HISTORY=False)
    def test_loan_history_requirement_can_be_disabled(self):
        review = ReviewService.create_review(user=self.user, book=self.book, rating=3)
        self.assertIsNotNone(review.pk)

    def test_duplicate_review_rejected_with_clean_validation_error(self):
        Loan.objects.create(user=self.user, book=self.book, due_date="2099-01-01")
        ReviewService.create_review(user=self.user, book=self.book, rating=4)
        with self.assertRaises(DRFValidationError):
            ReviewService.create_review(user=self.user, book=self.book, rating=2)
        # Still just one row — the duplicate attempt never reached the DB.
        self.assertEqual(
            Review.objects.filter(user=self.user, book=self.book).count(), 1
        )

    def test_update_review_mutates_in_place(self):
        Loan.objects.create(user=self.user, book=self.book, due_date="2099-01-01")
        review = ReviewService.create_review(user=self.user, book=self.book, rating=2)
        original_id = review.id

        updated = ReviewService.update_review(
            review=review, rating=5, comment="Changed my mind"
        )

        self.assertEqual(updated.id, original_id)
        self.assertEqual(updated.rating, 5)
        self.assertEqual(updated.comment, "Changed my mind")
        self.assertEqual(Review.objects.filter(book=self.book).count(), 1)

    def test_update_review_partial_leaves_other_field_untouched(self):
        Loan.objects.create(user=self.user, book=self.book, due_date="2099-01-01")
        review = ReviewService.create_review(
            user=self.user, book=self.book, rating=3, comment="Original"
        )
        ReviewService.update_review(review=review, rating=4, comment=None)
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Original")


# ---------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------
class ReviewAPITests(APITestCase):
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
        self.book = make_book(isbn="9780000000022")

        Loan.objects.create(user=self.member, book=self.book, due_date="2099-01-01")
        Loan.objects.create(user=self.other_member, book=self.book, due_date="2099-01-01")

    def _login(self, user, password="StrongPass123!"):
        response = self.client.post(
            "/api/v1/auth/login/", {"username": user.username, "password": password}
        )
        access = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_unauthenticated_cannot_list_reviews(self):
        response = self.client.get(f"/api/v1/books/{self.book.id}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_create_review_after_borrowing(self):
        self._login(self.member)
        response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/",
            {"rating": 5, "comment": "Loved it"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "member1")
        self.assertEqual(response.data["book"], self.book.id)

    def test_member_without_loan_cannot_create_review(self):
        never_borrowed = User.objects.create_user(
            username="never_borrowed",
            email="never_borrowed@example.com",
            password="StrongPass123!",
        )
        self._login(never_borrowed)
        response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 5}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_review_returns_400(self):
        self._login(self.member)
        self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 4}
        )
        response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_out_of_range_returns_400(self):
        self._login(self.member)
        response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 9}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_reviews_for_book(self):
        self._login(self.member)
        self.client.post(f"/api/v1/books/{self.book.id}/reviews/", {"rating": 5})
        self._login(self.other_member)
        self.client.post(f"/api/v1/books/{self.book.id}/reviews/", {"rating": 3})

        response = self.client.get(f"/api/v1/books/{self.book.id}/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

    def test_owner_can_update_own_review(self):
        self._login(self.member)
        create_response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        review_id = create_response.data["id"]

        response = self.client.patch(
            f"/api/v1/reviews/{review_id}/", {"rating": 5, "comment": "Updated"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["comment"], "Updated")

    def test_non_owner_cannot_update_review(self):
        self._login(self.member)
        create_response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        review_id = create_response.data["id"]

        self._login(self.other_member)
        response = self.client.patch(
            f"/api/v1/reviews/{review_id}/", {"rating": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_review(self):
        self._login(self.member)
        create_response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        review_id = create_response.data["id"]

        self._login(self.admin)
        response = self.client.delete(f"/api/v1/reviews/{review_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review_id).exists())

    def test_owner_can_delete_own_review(self):
        self._login(self.member)
        create_response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        review_id = create_response.data["id"]

        response = self.client.delete(f"/api/v1/reviews/{review_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_owner_cannot_delete_review(self):
        self._login(self.member)
        create_response = self.client.post(
            f"/api/v1/books/{self.book.id}/reviews/", {"rating": 2}
        )
        review_id = create_response.data["id"]

        self._login(self.other_member)
        response = self.client.delete(f"/api/v1/reviews/{review_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BookAverageRatingAPITests(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            username="rater1", email="rater1@example.com", password="StrongPass123!"
        )
        self.other_member = User.objects.create_user(
            username="rater2", email="rater2@example.com", password="StrongPass123!"
        )
        self.book = make_book(isbn="9780000000033")
        Loan.objects.create(user=self.member, book=self.book, due_date="2099-01-01")
        Loan.objects.create(user=self.other_member, book=self.book, due_date="2099-01-01")

    def _login(self, user, password="StrongPass123!"):
        response = self.client.post(
            "/api/v1/auth/login/", {"username": user.username, "password": password}
        )
        access = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_book_detail_shows_null_rating_with_no_reviews(self):
        self._login(self.member)
        response = self.client.get(f"/api/v1/books/books/{self.book.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["average_rating"])
        self.assertEqual(response.data["review_count"], 0)

    def test_book_detail_reflects_average_rating(self):
        self._login(self.member)
        self.client.post(f"/api/v1/books/{self.book.id}/reviews/", {"rating": 5})
        self._login(self.other_member)
        self.client.post(f"/api/v1/books/{self.book.id}/reviews/", {"rating": 3})

        response = self.client.get(f"/api/v1/books/books/{self.book.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_rating"], 4.0)
        self.assertEqual(response.data["review_count"], 2)
