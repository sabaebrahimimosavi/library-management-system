from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin
from .serializers import (
    DashboardStatisticsSerializer,
    MostBorrowedBookSerializer,
    MostActiveUserSerializer,
    MonthlyBorrowingSerializer,
    OverdueUserSerializer,
    PopularBookSerializer,
)
from .services import DashboardService


class DashboardStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = DashboardStatisticsSerializer

    def get(self, request):
        data = DashboardService.get_statistics()
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class MostBorrowedBooksView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = MostBorrowedBookSerializer

    def get_queryset(self):
        return DashboardService.get_most_borrowed_books()


class MostActiveUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = MostActiveUserSerializer

    def get_queryset(self):
        return DashboardService.get_most_active_users()


class OverdueUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = OverdueUserSerializer

    def get_queryset(self):
        return DashboardService.get_overdue_users()


class MonthlyBorrowingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = MonthlyBorrowingSerializer

    def get(self, request):
        queryset = DashboardService.get_monthly_borrowing_statistics()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PopularBooksView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = PopularBookSerializer

    def get_queryset(self):
        return DashboardService.get_most_popular_books()