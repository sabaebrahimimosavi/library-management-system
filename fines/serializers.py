from rest_framework import serializers

from .models import Fine, Payment


class FineSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    book_title = serializers.CharField(source="loan.book.title", read_only=True)
    loan_due_date = serializers.DateField(source="loan.due_date", read_only=True)

    class Meta:
        model = Fine
        fields = [
            "id",
            "loan",
            "user",
            "username",
            "book_title",
            "loan_due_date",
            "overdue_days",
            "daily_rate",
            "amount",
            "status",
            "paid_at",
            "waived_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "loan",
            "user",
            "overdue_days",
            "daily_rate",
            "amount",
            "status",
            "paid_at",
            "waived_at",
            "created_at",
            "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "fine",
            "user",
            "amount",
            "method",
            "status",
            "provider_reference",
            "created_at",
        ]
        read_only_fields = fields
