from django.contrib import admin

from .models import Fine


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "loan",
        "overdue_days",
        "daily_rate",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("user__username", "user__email", "loan__book__title")
    readonly_fields = (
        "loan",
        "user",
        "overdue_days",
        "daily_rate",
        "amount",
        "created_at",
        "updated_at",
    )