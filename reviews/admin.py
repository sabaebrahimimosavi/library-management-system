from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "book", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__username", "user__email", "book__title")
    readonly_fields = ("created_at", "updated_at")
