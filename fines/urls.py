from rest_framework.routers import DefaultRouter

from .views import FineViewSet

router = DefaultRouter()
router.register("", FineViewSet, basename="fine")

urlpatterns = router.urls
