from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from books.models import Book


COVERS_SUBDIR = Path("books") / "covers"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
}


class Command(BaseCommand):
    help = (
        "Connect existing cover files in "
        "media/books/covers to books using ISBN filenames."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving them.",
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            help=(
                "Replace the current cover_image value "
                "when an ISBN-named file exists."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        covers_directory = (
            Path(settings.MEDIA_ROOT)
            / COVERS_SUBDIR
        )

        if not covers_directory.exists():
            self.stderr.write(
                self.style.ERROR(
                    f"Directory does not exist: "
                    f"{covers_directory}"
                )
            )
            return

        files_by_isbn = {}

        for file_path in covers_directory.iterdir():
            if not file_path.is_file():
                continue

            if (
                file_path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            isbn = self.normalize_isbn(
                file_path.stem
            )

            if isbn:
                files_by_isbn[isbn] = file_path

        linked = 0
        skipped = 0
        not_found = 0

        books = Book.objects.exclude(
            isbn=""
        ).order_by("id")

        for book in books.iterator():
            isbn = self.normalize_isbn(
                book.isbn
            )

            matching_file = files_by_isbn.get(
                isbn
            )

            if not matching_file:
                not_found += 1
                continue

            if book.cover_image and not overwrite:
                skipped += 1
                continue

            relative_name = (
                COVERS_SUBDIR
                / matching_file.name
            ).as_posix()

            if dry_run:
                self.stdout.write(
                    f"Would link {book.title}: "
                    f"{relative_name}"
                )
            else:
                book.cover_image.name = (
                    relative_name
                )

                book.save(
                    update_fields=[
                        "cover_image"
                    ]
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Linked {book.title}: "
                        f"{relative_name}"
                    )
                )

            linked += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would link' if dry_run else 'Linked'} "
                f"{linked} cover(s)."
            )
        )

        self.stdout.write(
            f"Skipped existing fields: {skipped}"
        )

        self.stdout.write(
            f"No matching ISBN file: {not_found}"
        )

    @staticmethod
    def normalize_isbn(value):
        if not value:
            return ""

        return "".join(
            character
            for character in str(value)
            if character.isalnum()
        ).upper()