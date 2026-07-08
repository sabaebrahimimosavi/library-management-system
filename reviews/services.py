"""
ReviewService is intentionally small: reviews don't have the
multi-state lifecycle fines/reservations have (no PENDING/SETTLED
transitions), just create-with-validation and in-place update. The two
checks in create_review are the only real business rules:

  1. one review per (user, book) — checked here (not left to the DB
     constraint alone) so a duplicate attempt returns a clean 400 with
     a message instead of surfacing an IntegrityError as a 500.
  2. the loan-history requirement — see the design note in
     reviews/models.py. Gated behind REVIEWS_REQUIRE_LOAN_HISTORY so
     it's a one-line settings change to disable, not a code change.
"""

from django.conf import settings
from rest_framework.exceptions import ValidationError

from loans.models import Loan

from .models import Review


class ReviewService:
    @staticmethod
    def _has_borrowed(*, user, book) -> bool:
        return Loan.objects.filter(user=user, book=book).exists()

    @classmethod
    def create_review(cls, *, user, book, rating, comment=""):
        if Review.objects.filter(user=user, book=book).exists():
            raise ValidationError(
                {"detail": "You have already reviewed this book."}
            )

        if getattr(settings, "REVIEWS_REQUIRE_LOAN_HISTORY", True):
            if not cls._has_borrowed(user=user, book=book):
                raise ValidationError(
                    {"detail": "You can only review books you have borrowed."}
                )

        return Review.objects.create(
            user=user, book=book, rating=rating, comment=comment
        )

    @staticmethod
    def update_review(*, review, rating=None, comment=None):
        update_fields = []

        if rating is not None:
            review.rating = rating
            update_fields.append("rating")

        if comment is not None:
            review.comment = comment
            update_fields.append("comment")

        if update_fields:
            update_fields.append("updated_at")
            review.save(update_fields=update_fields)

        return review
