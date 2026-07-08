from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    `user` and `book` are read-only here on purpose: `user` always comes
    from the authenticated requester and `book` always comes from the
    URL (`/api/v1/books/{book_id}/reviews/`), never from the request
    body — same pattern fines/notifications use for `user`. Rating
    min/max (1-5) is enforced automatically: DRF's ModelSerializer picks
    up the MinValueValidator/MaxValueValidator already declared on
    Review.rating.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "book",
            "book_title",
            "user",
            "username",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "book",
            "user",
            "created_at",
            "updated_at",
        ]
