"""
Two entry points, matching the URL shape specified in the phase 6
handover:

  GET/POST /api/v1/books/{book_id}/reviews/   -> BookReviewListCreateView
  GET/PATCH/DELETE /api/v1/reviews/{id}/       -> ReviewViewSet

Reading is open to any authenticated user (consistent with books/loans/
fines — this project doesn't have anonymous-read anywhere). Writing is
owner-or-admin for edit/delete; creation just requires being
authenticated (not IsMember) — nothing in the spec says admins can't
review books, unlike catalog writes which are deliberately
member-read-only. Tighten to IsMember here if that turns out to be
wrong.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, viewsets

from accounts.permissions import IsOwnerOrAdmin
from books.models import Book

from .models import Review
from .serializers import ReviewSerializer
from .services import ReviewService


class BookReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_book(self):
        return get_object_or_404(Book, pk=self.kwargs["book_id"])

    def get_queryset(self):
        return (
            Review.objects.filter(book_id=self.kwargs["book_id"])
            .select_related("user", "book")
        )

    def perform_create(self, serializer):
        book = self.get_book()
        review = ReviewService.create_review(
            user=self.request.user,
            book=book,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )
        # Bypassing serializer.save()/Review.objects.create() here since
        # ReviewService already created the row with its validation
        # (duplicate + loan-history checks) — this just points the
        # serializer at the result so the response body is correct.
        serializer.instance = review


class ReviewViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Review.objects.select_related("user", "book")
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        # serializer.instance is already the object get_object() fetched
        # for this request — ReviewService mutates and saves that same
        # instance in place, so no re-fetch/refresh is needed afterward.
        ReviewService.update_review(
            review=serializer.instance,
            rating=serializer.validated_data.get("rating"),
            comment=serializer.validated_data.get("comment"),
        )
