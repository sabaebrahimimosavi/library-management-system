from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookReviewListCreateView, ReviewViewSet

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path(
        "books/<int:book_id>/reviews/",
        BookReviewListCreateView.as_view(),
        name="book-review-list",
    ),
    path("", include(router.urls)),
]
