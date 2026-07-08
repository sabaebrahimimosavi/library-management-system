from rest_framework import serializers


class DashboardStatisticsSerializer(serializers.Serializer):
    total_books = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    overdue_loans = serializers.IntegerField()
    available_books = serializers.IntegerField()
    total_loans = serializers.IntegerField()
    pending_reservations = serializers.IntegerField()
    total_fines_collected = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    total_fines_outstanding = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


class MostBorrowedBookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    loan_count = serializers.IntegerField()


class MostActiveUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    loan_count = serializers.IntegerField()


class OverdueUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    overdue_loans = serializers.IntegerField()
    outstanding_fines = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
    )


class MonthlyBorrowingSerializer(serializers.Serializer):
    month = serializers.DateTimeField()
    count = serializers.IntegerField()


class PopularBookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    average_rating = serializers.FloatField()
    review_count = serializers.IntegerField()