from django.db import models

from django.core.exceptions import ValidationError

from datetime import date


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    publication_year = models.PositiveIntegerField()

    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="books/covers/",
        blank=True,
        null=True
    )

    copies = models.PositiveIntegerField(default=0)
    available_copies = models.PositiveIntegerField(default=0)

    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
    )

    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        related_name="books",
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="books",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["isbn"]),
        ]

    def clean(self):
        if self.available_copies > self.copies:
            raise ValidationError({
                "available_copies": (
                    "Available copies cannot exceed total copies."
                )
            })
        if self.publication_year > date.today().year:
            raise ValidationError({
                "publication_year": "Publication year cannot be in the future."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title