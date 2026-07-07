from django.contrib import admin

from .models import (
    Author,
    Genre,
    Publisher,
    Book,
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "nationality")
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "isbn",
        "copies",
        "available_copies",
    )

    search_fields = (
        "title",
        "isbn",
    )

    list_filter = (
        "genre",
        "publisher",
    )