from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import filters
from accounts.permissions import IsAdminOrReadOnly
from .pagination import BookPagination, LookupPagination

from .models import (
    Author,
    Genre,
    Publisher,
    Book,
)

from .serializers import (
    AuthorSerializer,
    GenreSerializer,
    PublisherSerializer,
    BookSerializer,
)

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LookupPagination

    search_fields = ["name"]
    filter_backends = [SearchFilter]

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LookupPagination

    search_fields = ["name"]
    filter_backends = [SearchFilter]

class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LookupPagination

    search_fields = ["name"]
    filter_backends = [SearchFilter]

class BookViewSet(viewsets.ModelViewSet):
    queryset = (
        Book.objects
        .select_related(
            "author",
            "genre",
            "publisher",
        )
        .annotate(
            average_rating_annotated=Avg("reviews__rating"),
            review_count_annotated=Count("reviews", distinct=True),
        )
        .all()
    )

    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = BookPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "author",
        "genre",
        "publisher",
        "publication_year",
    ]

    search_fields = [
        "title",
        "isbn",
        "author__name",
        "publisher__name",
        "genre__name",
    ]

    ordering_fields = [
        "title",
        "publication_year",
        "created_at",
    ]

    ordering = ["title"]

