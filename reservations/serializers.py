from rest_framework import serializers

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "user",
            "book",
            "status",
            "reserved_at",
            "fulfilled_at",
            "cancelled_at",
            "expires_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "reserved_at",
            "fulfilled_at",
            "cancelled_at",
            "expires_at",
        ]
