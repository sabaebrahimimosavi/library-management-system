from rest_framework.routers import DefaultRouter

from .views import (
    AuthorViewSet,
    GenreViewSet,
    PublisherViewSet,
    BookViewSet,
)

router = DefaultRouter()

router.register(
    "authors",
    AuthorViewSet,
)

router.register(
    "genres",
    GenreViewSet,
)

router.register(
    "publishers",
    PublisherViewSet,
)

router.register(
    "books",
    BookViewSet,
)

urlpatterns = router.urls