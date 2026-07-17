"""
1. One Review per (user, book) — UniqueConstraint, same pattern already
   used by reservations/loans for "one pending reservation per
   user+book". Editing is done via PATCH on the existing row, not by
   creating a new one, so `created_at` stays the original review date
   and `updated_at` reflects the last edit.

2. Whether a review requires having borrowed the book: yes, by default.
   ReviewService checks for any Loan record (active or returned — not
   requiring the loan be closed, so someone partway through reading
   isn't blocked from reviewing) before allowing a review to be
   created. This is gated behind `settings.REVIEWS_REQUIRE_LOAN_HISTORY`
   (default True) rather than hard-coded, so it can be turned off with
   a one-line settings change if product decides open reviews are
   preferred — see reviews/services.py.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                name="unique_review_per_user_book",
            )
        ]
        indexes = [
            models.Index(fields=["book", "rating"]),
        ]

    def __str__(self):
        return f"Review(book={self.book_id}, user={self.user_id}) {self.rating}/5"
