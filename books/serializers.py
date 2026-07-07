from rest_framework import serializers
from datetime import date
from .models import (
    Author,
    Genre,
    Publisher,
    Book,
)


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "biography",
            "birth_date",
            "nationality",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "website",
            "email",
            "phone",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.name",
        read_only=True
    )

    genre_name = serializers.CharField(
        source="genre.name",
        read_only=True
    )

    publisher_name = serializers.CharField(
        source="publisher.name",
        read_only=True
    )
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "isbn",
            "publication_year",
            "description",
            "cover_image",
            "copies",
            "available_copies",
            "author",
            "genre",
            "publisher",
            "created_at",
            "updated_at",
            "author_name",
            "genre_name",
            "publisher_name",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """
        Handle partial updates while keeping validation consistent.
        Model.clean() will also be called by model.save().
        """
        copies = attrs.get(
            "copies",
            self.instance.copies if self.instance else 0,
        )

        available_copies = attrs.get(
            "available_copies",
            self.instance.available_copies if self.instance else 0,
        )

        publication_year = attrs.get(
            "publication_year",
            self.instance.publication_year if self.instance else None,
        )

        if available_copies > copies:
            raise serializers.ValidationError(
                {
                    "available_copies": (
                        "Available copies cannot exceed total copies."
                    )
                }
            )

        

        if (
            publication_year is not None
            and publication_year > date.today().year
        ):
            raise serializers.ValidationError(
                {
                    "publication_year": (
                        "Publication year cannot be in the future."
                    )
                }
            )

        return attrs