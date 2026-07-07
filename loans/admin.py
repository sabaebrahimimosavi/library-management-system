from django.contrib import admin

from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "book",
        "status",
        "borrowed_at",
        "due_date",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "user__username",
        "book__title",
    )