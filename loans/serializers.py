from rest_framework import serializers
from .models import Loan
from datetime import date

class LoanSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    book_title = serializers.CharField(
        source="book.title",
        read_only=True,
    )

    class Meta:
        model = Loan
        fields = [
            "id",
            "user",
            "username",
            "book",
            "book_title",
            "borrowed_at",
            "due_date",
            "returned_at",
            "status",
        ]

        read_only_fields = [
            "id",
            "user",
            "borrowed_at",
            "returned_at",
            "status",
        ]

class BorrowBookSerializer(
    serializers.Serializer
):

    book = serializers.IntegerField()

    due_date = serializers.DateField()

    def validate_due_date(
        self,
        value,
    ):
        if value <= date.today():
            raise serializers.ValidationError(
                "Due date must be in the future."
            )

        return value

class ReturnLoanSerializer(
    serializers.Serializer
):
    pass