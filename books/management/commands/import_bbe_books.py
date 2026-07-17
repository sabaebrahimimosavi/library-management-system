"""
books/management/commands/import_bbe_books.py

Imports Authors, Genres, Publishers, and Books from the Goodreads
"Best Books Ever" dataset:
    https://github.com/scostap/goodreads_bbe_dataset
    (CSV: Best_Books_Ever_dataset/books_1.Best_Books_Ever.csv)

That dataset has ~52,000 rows and richer relationships than this
project's schema supports (multiple authors/genres per book, no
required publisher, no unique-ISBN guarantee), so this command makes
some simplifying decisions on the way in:

  - author:    only the FIRST author listed is used (Book.author is a
               single ForeignKey, not many-to-many).
  - genres:    only the FIRST genre listed is used, same reason. Rows
               with no parseable genre fall back to an "Uncategorized"
               Genre so the required FK is never left unset.
  - publisher: rows with a blank publisher fall back to an "Unknown"
               Publisher, since Book.publisher is required.
  - isbn:      required + unique on Book. Rows with no ISBN, or an
               ISBN already seen (in this run or already in the DB),
               are skipped.
  - publication_year: parsed out of the dataset's publishDate column,
               which has two different formats depending on which half
               of the scrape a row came from (mm/dd/yyyy for the first
               ~30k rows, "Month Day, Year" for the rest — see the
               dataset's own README). Rows where no year can be parsed,
               or where the year is in the future (fails
               Book.clean()), are skipped.
  - pages:     new optional field — best effort int parse, left NULL
               if missing/unparseable.

Usage:
    # Preview without writing anything:
    python manage.py import_bbe_books --limit 500 --dry-run

    # Actually import the first 500 usable rows, 3 copies each:
    python manage.py import_bbe_books --limit 500 --copies 3

    # Same, but also download & attach each book's cover image:
    python manage.py import_bbe_books --limit 500 --with-images

    # Re-run against a file you already downloaded (faster, repeatable):
    python manage.py import_bbe_books --source ./books_1.Best_Books_Ever.csv --limit 2000

Notes:
  - The dataset is CC BY-NC 4.0 (Casanova Lozano & Costa Planells,
    2020) — fine for coursework/personal projects, not for commercial
    resale.
  - This downloads/reads a large CSV and does a get_or_create per row,
    so don't run it with a huge --limit on first try; start small
    (a few hundred) and raise it once you've confirmed the mapping
    looks right in your admin/frontend.
"""

import ast
import csv
import io
import mimetypes
import re
import urllib.request
from datetime import date
from typing import Optional
from urllib.error import URLError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from books.models import Author, Book, Genre, Publisher

DEFAULT_SOURCE = (
    "https://raw.githubusercontent.com/scostap/goodreads_bbe_dataset/"
    "main/Best_Books_Ever_dataset/books_1.Best_Books_Ever.csv"
)

UNCATEGORIZED_GENRE = "Uncategorized"
UNKNOWN_PUBLISHER = "Unknown"

DATE_FORMATS = ["%m/%d/%Y", "%B %d, %Y", "%B %d %Y", "%m/%d/%y"]

YEAR_RE = re.compile(r"(1[4-9]\d{2}|20\d{2})")


class Command(BaseCommand):
    help = (
        "Imports Authors, Genres, Publishers, and Books from the "
        "Goodreads Best Books Ever CSV dataset."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help=(
                "URL or local file path to the CSV. Defaults to the "
                "raw GitHub URL. Pass a local path (after downloading "
                "once) for faster, repeatable runs."
            ),
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Max number of books to CREATE (not rows read). Default 500.",
        )
        parser.add_argument(
            "--copies",
            type=int,
            default=3,
            help="copies (== available_copies) to set on every imported book. Default 3.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report what would happen without writing to the DB.",
        )
        parser.add_argument(
            "--with-images",
            action="store_true",
            help=(
                "Also download each book's coverImg and attach it as "
                "cover_image. Slower — one extra HTTP request per book. "
                "A failed/missing image never blocks the book from being "
                "created, it's just left without a cover."
            ),
        )
        parser.add_argument(
            "--image-timeout",
            type=int,
            default=10,
            help="Seconds to wait per cover image download. Default 10.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        limit = options["limit"]
        copies = options["copies"]
        dry_run = options["dry_run"]
        with_images = options["with_images"]
        image_timeout = options["image_timeout"]

        raw_text = self._load_source(source)
        reader = csv.DictReader(io.StringIO(raw_text))

        existing_isbns = set(Book.objects.values_list("isbn", flat=True))
        seen_isbns = set()
        author_cache = {}
        genre_cache = {}
        publisher_cache = {}

        created = 0
        images_set = 0
        images_failed = 0
        skipped = {
            "no_isbn": 0,
            "duplicate_isbn": 0,
            "no_title": 0,
            "no_author": 0,
            "bad_year": 0,
            "isbn_too_long": 0,
            "other_error": 0,
        }

        for row in reader:
            if created >= limit:
                break

            title = (row.get("title") or "").strip()[:255]
            if not title:
                skipped["no_title"] += 1
                continue

            isbn = (row.get("isbn") or "").strip()
            if not isbn:
                skipped["no_isbn"] += 1
                continue
            if len(isbn) > 20:
                skipped["isbn_too_long"] += 1
                continue
            if isbn in existing_isbns or isbn in seen_isbns:
                skipped["duplicate_isbn"] += 1
                continue

            author_name = self._first_author(row.get("author"))
            if not author_name:
                skipped["no_author"] += 1
                continue

            year = self._parse_year(row.get("publishDate"))
            if year is None or year > date.today().year:
                skipped["bad_year"] += 1
                continue

            genre_name = self._first_genre(row.get("genres")) or UNCATEGORIZED_GENRE
            publisher_name = (row.get("publisher") or "").strip()[:255] or UNKNOWN_PUBLISHER
            pages = self._parse_pages(row.get("pages"))
            description = (row.get("description") or "").strip()

            seen_isbns.add(isbn)

            if dry_run:
                created += 1
                continue

            try:
                with transaction.atomic():
                    author = self._get_cached(
                        author_cache, author_name, Author, name=author_name
                    )
                    genre = self._get_cached(
                        genre_cache, genre_name, Genre, name=genre_name
                    )
                    publisher = self._get_cached(
                        publisher_cache, publisher_name, Publisher, name=publisher_name
                    )

                    book = Book.objects.create(
                        title=title,
                        isbn=isbn,
                        publication_year=year,
                        description=description,
                        pages=pages,
                        copies=copies,
                        available_copies=copies,
                        author=author,
                        genre=genre,
                        publisher=publisher,
                    )
                created += 1

                if with_images:
                    cover_url = (row.get("coverImg") or "").strip()
                    if cover_url and self._attach_cover_image(book, cover_url, image_timeout):
                        images_set += 1
                    elif cover_url:
                        images_failed += 1
            except (ValidationError, IntegrityError) as exc:
                skipped["other_error"] += 1
                self.stderr.write(f"  skipped '{title}' ({isbn}): {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] Would have created' if dry_run else 'Created'} "
            f"{created} book(s)."
        ))
        if with_images:
            self.stdout.write(f"Cover images: {images_set} set, {images_failed} failed/missing.")
        self.stdout.write("Skipped: " + ", ".join(f"{k}={v}" for k, v in skipped.items()))

    # -- helpers -----------------------------------------------------

    def _load_source(self, source: str) -> str:
        if source.startswith("http://") or source.startswith("https://"):
            self.stdout.write(f"Downloading {source} ...")
            try:
                req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except URLError as exc:
                raise CommandError(f"Could not download {source}: {exc}")
        try:
            with open(source, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError as exc:
            raise CommandError(f"Could not read {source}: {exc}")

    @staticmethod
    def _get_cached(cache: dict, key: str, model, **kwargs):
        if key not in cache:
            obj, _ = model.objects.get_or_create(**kwargs)
            cache[key] = obj
        return cache[key]

    @staticmethod
    def _first_author(raw: Optional[str]) -> str:
        if not raw:
            return ""
        # BBE 'author' values are sometimes "Name1, Name2 (Illustrator)";
        # take the first comma-separated segment and strip any trailing
        # parenthetical role.
        first = raw.split(",")[0]
        first = re.sub(r"\s*\([^)]*\)\s*$", "", first).strip()
        return first[:255]

    @staticmethod
    def _first_genre(raw: Optional[str]) -> str:
        if not raw:
            return ""
        try:
            genres = ast.literal_eval(raw)
            if isinstance(genres, (list, tuple)) and genres:
                return str(genres[0]).strip()[:100]
        except (ValueError, SyntaxError):
            pass
        return ""

    @staticmethod
    def _parse_year(raw: Optional[str]):
        if not raw:
            return None
        raw = raw.strip()
        for fmt in DATE_FORMATS:
            try:
                from datetime import datetime
                return datetime.strptime(raw, fmt).year
            except ValueError:
                continue
        match = YEAR_RE.search(raw)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _parse_pages(raw: Optional[str]):
        if not raw:
            return None
        match = re.search(r"\d+", str(raw))
        return int(match.group(0)) if match else None

    @staticmethod
    def _attach_cover_image(book: Book, url: str, timeout: int) -> bool:
        """
        Downloads `url` and saves it as book.cover_image. Returns True on
        success. Never raises — a bad/missing cover should never stop the
        rest of the import.
        """
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_type = resp.headers.get("Content-Type", "")
                data = resp.read()
        except (URLError, OSError, ValueError):
            return False

        if not data:
            return False

        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".jpg"
        if ext == ".jpe":
            ext = ".jpg"
        filename = f"{book.isbn or book.pk}{ext}"

        try:
            book.cover_image.save(filename, ContentFile(data), save=True)
        except Exception:
            return False
        return True