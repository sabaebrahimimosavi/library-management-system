"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve as static_serve

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/v1/auth/", 
        include("accounts.urls")
    ),

    path(
        "api/v1/auth/login/",
        TokenObtainPairView.as_view(),
    ),

    path(
        "api/v1/auth/refresh/",
        TokenRefreshView.as_view(),
    ),

    path(
        "api/schema/", 
        SpectacularAPIView.as_view(), 
        name="schema"
        ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    path(
        "api/v1/books/", 
        include("books.urls")
    ),

    path(
        "api/v1/loans/",
        include("loans.urls"),
    ),

    path(
        "api/v1/",
         include("reservations.urls")
    ),

    path(
        "api/v1/notifications/",
         include("notifications.urls")
    ),

    path(
        "api/v1/fines/",
         include("fines.urls")
    ),

    path(
        "api/v1/",
         include("reviews.urls")
    ),

    path(
        "api/v1/dashboard/", 
        include("dashboard.urls")
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ---------------------------------------------------------------------------
# Serve the frontend (frontend/index.html, css/, js/) from the same Django
# dev server, so the whole app runs off one port (http://127.0.0.1:8000)
# instead of a separate `python -m http.server 5500`.
#
# Dev-only: this uses Django's built-in static file server, which is not
# meant for production. In production you'd serve these files via nginx /
# whitenoise / a CDN instead.
# ---------------------------------------------------------------------------
FRONTEND_DIR = settings.BASE_DIR / "frontend"

urlpatterns += [
    # /css/theme.css, /js/app.js, /js/views/..., etc.
    re_path(
        r"^(?P<path>(?:css|js)/.*)$",
        static_serve,
        {"document_root": FRONTEND_DIR},
    ),
    # Root URL -> frontend/index.html
    re_path(
        r"^$",
        static_serve,
        {"document_root": FRONTEND_DIR, "path": "index.html"},
    ),
]