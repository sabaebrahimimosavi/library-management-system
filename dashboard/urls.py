from django.urls import path

from .views import (
    DashboardStatsView,
    MonthlyBorrowingView,
    MostActiveUsersView,
    MostBorrowedBooksView,
    OverdueUsersView,
    PopularBooksView,
)

urlpatterns = [
    path(
        "stats/",
        DashboardStatsView.as_view(),
        name="dashboard-stats",
    ),
    path(
        "reports/most-borrowed/",
        MostBorrowedBooksView.as_view(),
        name="most-borrowed-books",
    ),
    path(
        "reports/most-active-users/",
        MostActiveUsersView.as_view(),
        name="most-active-users",
    ),
    path(
        "reports/overdue-users/",
        OverdueUsersView.as_view(),
        name="overdue-users",
    ),
    path(
        "reports/monthly-borrowing/",
        MonthlyBorrowingView.as_view(),
        name="monthly-borrowing",
    ),
    path(
    "reports/popular-books/",
    PopularBooksView.as_view(),
    name="popular-books",
    ),
]