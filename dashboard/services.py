from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

from books.models import Book
from fines.models import Fine
from loans.models import Loan
from reservations.models import Reservation

from django.db.models import Count, Q, Sum, Avg, F

User = get_user_model()


class DashboardService:
    """
    Read-only service that provides aggregated statistics and reports
    for the administrative dashboard.
    """

    @staticmethod
    def get_statistics():
        """
        Return the overall dashboard statistics.
        """
        return {
            "total_books": Book.objects.count(),
            "total_users": User.objects.count(),
            "active_loans": Loan.objects.filter(
                status=Loan.Status.ACTIVE
            ).count(),
            "overdue_loans": Loan.objects.filter(
                status=Loan.Status.OVERDUE
            ).count(),
            "total_loans": Loan.objects.count(),
            "available_books": (
                Book.objects.aggregate(
                    total=Sum("available_copies")
                )["total"] or 0
            ),
            "pending_reservations": Reservation.objects.filter(
                status=Reservation.Status.PENDING
            ).count(),
            "total_fines_collected": (
                Fine.objects.filter(status=Fine.Status.PAID)
                .aggregate(total=Sum("amount"))
                .get("total")
                or 0
            ),
            "total_fines_outstanding": (
                Fine.objects.filter(status=Fine.Status.UNPAID)
                .aggregate(total=Sum("amount"))
                .get("total")
                or 0
            ),
        }

    @staticmethod
    def get_most_popular_books():
        return (
            Book.objects.annotate(
                average_rating=Avg("reviews__rating"),
                review_count=Count("reviews"),
            )
            .order_by(
                F("average_rating").desc(nulls_last=True),
                 "-review_count",
                 "title",
            )
        )

    @staticmethod
    def get_most_borrowed_books():
        """
        Return books ordered by number of loans.
        """
        return (
            Book.objects.annotate(
                loan_count=Count("loans")
            )
            .order_by("-loan_count", "title")
        )

    @staticmethod
    def get_most_active_users():
        """
        Return users ordered by number of loans.
        """
        return (
            User.objects.annotate(
                loan_count=Count("loans")
            )
            .order_by("-loan_count", "username")
        )

    @staticmethod
    def get_overdue_users():
        """
        Return users who currently have overdue loans.
        """
        return (
    User.objects.filter(loans__status=Loan.Status.OVERDUE)
    .annotate(
        overdue_loans=Count(
            "loans",
            filter=Q(loans__status=Loan.Status.OVERDUE),
            distinct=True,
        ),
        outstanding_fines=Sum(
            "loans__fine__amount",
            filter=Q(loans__fine__status=Fine.Status.UNPAID),
        ),
    )
    .distinct()
    .order_by("-overdue_loans", "username")
)

    @staticmethod
    def get_monthly_borrowing_statistics():
        """
        Return monthly borrowing totals in a chart-friendly format.
        """
        return (
            Loan.objects.annotate(
                month=TruncMonth("borrowed_at")
            )
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )