# Online Library Management System

A full-stack library management application for managing books, members, borrowing, returns, reservations, fines, notifications, reviews, and administrative reports.

The project uses Django and Django REST Framework for the backend, PostgreSQL for data storage, and a Vue 3 single-page frontend served directly by Django.

## Features

### Authentication and user roles

- Member registration and JWT authentication
- Password reset by email
- Profile and password management
- Two application roles:
  - `ADMIN` — library administrator
  - `MEMBER` — regular library member
- Protected frontend routes based on authentication and role
- Integrated Django Admin access for library administrators
- Members and unauthenticated visitors receive a permission-denied page when trying to open `/django-admin/`

### Book catalog

- Add, edit, view, and search books
- Filter by title, author, genre, and publication year
- Sort by title or publication year
- 20 books per catalog page
- Direct page-number navigation in addition to Previous and Next buttons
- Catalog state is preserved when opening a book and returning to the list
- Book information includes:
  - Title
  - ISBN
  - Author
  - Genre
  - Publisher
  - Publication year
  - Page count
  - Description
  - Total copies
  - Available copies
  - Cover image
  - Average rating and review count

### Borrowing and returns

- Members can borrow available books
- A configurable loan period is used to calculate due dates
- Available inventory is updated transactionally
- Members can view their own loan history
- Administrators can view all loans
- Returned books automatically increase available inventory
- Overdue loans are transitioned to the `OVERDUE` state

### Reservations

- Members can reserve books only when all copies are unavailable
- Duplicate pending reservations for the same member and book are prevented
- Members can cancel pending reservations
- Reservations are marked fulfilled when the member borrows the book
- Waiting members are notified when a returned copy becomes available

### Fines and payments

- Overdue fines are calculated from the number of overdue days
- One fine is maintained per loan and recalculated while the loan remains overdue
- Members can view and pay their own fines
- When fine is paied, The book will be returned automatically 
- Administrators can view all fines and waive unpaid fines
- Payment attempts are stored for audit history

> The current payment gateway is a mock implementation for development and demonstration. It must be replaced with a real payment provider before production use.

### Notifications

- Due-in-two-days reminders
- Due-today reminders
- Reservation availability notifications
- Fine-issued notifications
- Fine-payment confirmations
- Read/unread notification state
- Email delivery through SMTP

### Ratings and reviews

- Ratings from 1 to 5
- One review per user and book
- Review editing and deletion
- Reviews can optionally require prior loan history
- Average ratings and review counts are displayed in the catalog

### Administrative dashboard

- Total books and users
- Active and overdue loans
- Available inventory
- Pending reservations
- Outstanding and collected fines
- Most borrowed books
- Most active members
- Overdue members
- Monthly borrowing statistics
- Popular books by ratings and review count

### Data and cover utilities

The project includes two custom Django management commands:

- `import_bbe_books` — imports books from the Goodreads Best Books Ever dataset
- `link_existing_covers` — connects ISBN-named files from `media/books/covers/` to the matching database records

---

## Technology stack

### Backend

- Python
- Django 4.2
- Django REST Framework
- Simple JWT
- PostgreSQL
- django-filter
- drf-spectacular
- Pillow
- python-decouple

### Frontend

- Vue 3
- Vue Router
- Bootstrap 5
- Bootstrap Icons
- Plain JavaScript ES modules

The frontend does not require Node.js or a build step. Vue, Vue Router, and Bootstrap are loaded through CDNs, while Django serves the local frontend files.

### Optional background processing

- Celery
- Redis
- Celery Beat

---

## Project structure

```text
library_management/
├── accounts/              # Users, authentication, roles, password reset
├── books/                 # Books, authors, genres, publishers, import commands
├── dashboard/             # Administrative statistics and reports
├── fines/                 # Fine calculation, payments, and related tasks
├── frontend/              # Vue application, CSS, components, and views
├── loans/                 # Borrowing and return workflow
├── notifications/         # In-app and email notifications
├── reservations/          # Book reservation workflow
├── reviews/               # Ratings and reviews
├── core/                  # Django settings, URLs, Celery, ASGI, and WSGI
├── media/                 # Runtime cover images; not committed to Git
├── manage.py
├── requirements.txt
└── README.md
```

---

## Prerequisites

Install the following before running the project:

- Python 3.8 or later
- PostgreSQL
- Git
- Redis only when using Celery background workers

The project has primarily been developed on Windows, but it can also run on Linux and macOS.

---

## Installation

### 1. Clone the repository

```bash
git clone <REPOSITORY_URL>
cd library_management
```

### 2. Create a virtual environment

#### Windows Command Prompt

```cmd
python -m venv venv
venv\Scripts\activate
```

#### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux or macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The Django settings use `corsheaders`. Ensure this package exists in `requirements.txt`:

```text
django-cors-headers
```

When Celery scheduling is enabled, also install and record:

```text
celery
redis
```

You can verify the environment with:

```bash
python -m pip check
```

---

## PostgreSQL setup

Create a PostgreSQL database and user. Example SQL:

```sql
CREATE DATABASE library_management;
CREATE USER library_user WITH PASSWORD 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON DATABASE library_management TO library_user;
```

The exact PostgreSQL commands may vary depending on your local configuration and PostgreSQL version.

---

## Environment variables

Create a file named `.env` in the project root, beside `manage.py`:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=True

DB_NAME=library_management
DB_USER=library_user
DB_PASSWORD=replace-with-your-database-password
DB_HOST=localhost
DB_PORT=5432

EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

FRONTEND_BASE_URL=http://127.0.0.1:8000
PASSWORD_RESET_TIMEOUT=3600
DAILY_FINE_AMOUNT=0.50

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Do not commit `.env` to Git.

For Gmail SMTP, use a Google App Password rather than your normal account password.

---

## Database initialization

Apply migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

Because the custom user model also contains an application role, ensure the administrator has the `ADMIN` role and Django staff access:

```bash
python manage.py shell -c "from accounts.models import User; u=User.objects.get(username='YOUR_USERNAME'); u.role=User.Roles.ADMIN; u.is_staff=True; u.is_superuser=True; u.save()"
```

Replace `YOUR_USERNAME` with the username created by `createsuperuser`.

---

## Running the application

Start the Django development server:

```bash
python manage.py runserver
```

Open the application:

```text
http://127.0.0.1:8000/
```

Useful development URLs:

```text
Application:       http://127.0.0.1:8000/
Django Admin:      http://127.0.0.1:8000/django-admin/
Swagger API docs:  http://127.0.0.1:8000/api/docs/
ReDoc API docs:    http://127.0.0.1:8000/api/redoc/
OpenAPI schema:    http://127.0.0.1:8000/api/schema/
```

Use the same host consistently. Avoid switching between `localhost` and `127.0.0.1`, because browser cookies are stored separately for each hostname.

### Django Admin behavior

- Logging into the library with an administrator account also creates the Django session needed for `/django-admin/`.
- The Admin menu in the navbar contains a direct Django Admin link.
- Regular members and guests cannot access `/django-admin/` and receive a permission-denied page.
- Logging into the application as a member clears any previous Django administrator session in that browser.

---

## Importing sample books

The `import_bbe_books` command imports books from the Goodreads Best Books Ever dataset.

Preview an import without changing the database:

```bash
python manage.py import_bbe_books --limit 500 --dry-run
```

Import 500 books with three copies each:

```bash
python manage.py import_bbe_books --limit 500 --copies 3
```

Import from a local CSV file:

```bash
python manage.py import_bbe_books --source ./books_1.Best_Books_Ever.csv --limit 500 --copies 3
```

Attempt to import cover images from the dataset:

```bash
python manage.py import_bbe_books --limit 500 --copies 3 --with-images
```

The importer uses the first available author and genre because the current database schema stores one author and one genre per book. Rows without a usable ISBN, title, author, or publication year are skipped.

### Dataset attribution

The import command uses the Goodreads Best Books Ever dataset by Casanova Lozano and Costa Planells. The dataset is published under CC BY-NC 4.0 and should not be used for unauthorized commercial resale.

---

## Linking local cover images

Cover files should be placed in:

```text
media/books/covers/
```

Name each image using the book ISBN:

```text
media/books/covers/9780451524935.jpg
media/books/covers/9781451627282.png
```

Supported extensions include JPEG, PNG, WebP, and GIF.

Preview the database links:

```bash
python manage.py link_existing_covers --dry-run
```

Apply the links:

```bash
python manage.py link_existing_covers
```

Replace stale or incorrect database image paths:

```bash
python manage.py link_existing_covers --overwrite
```

The command updates the database reference only. It does not duplicate or delete the local image files.

---

## Fine and reminder jobs

During local development, starting `runserver` performs these checks once:

- Calculates overdue fines
- Sends due-date reminder notifications when needed

They can also be executed manually:

```bash
python manage.py calculate_fines
python manage.py send_due_date_reminders
```

Both operations are designed to be safe to run repeatedly.

### Celery worker and scheduler

For production-like scheduled execution, start Redis and run:

```bash
celery -A core worker -l info
```

On Windows, the worker may require:

```cmd
celery -A core worker -l info -P solo
```

Start Celery Beat in another terminal:

```bash
celery -A core beat -l info
```

The configured schedule runs:

- Fine calculation daily at 01:00 server time
- Due-date reminders daily at 08:00 server time

Do not run duplicate schedulers in production, or the same periodic job may be triggered more than once.

---

## Running tests

Run all tests:

```bash
python manage.py test
```

Run tests for a specific app:

```bash
python manage.py test accounts
python manage.py test loans
python manage.py test reservations
python manage.py test fines
python manage.py test reviews
python manage.py test dashboard
```

Run Django’s configuration checks:

```bash
python manage.py check
```

---

## API authentication

The REST API uses JWT authentication.

A successful login returns access and refresh tokens. Protected API requests send the access token as:

```http
Authorization: Bearer <access-token>
```

The frontend manages these tokens automatically.

Main API groups include:

```text
/api/v1/auth/
/api/v1/books/
/api/v1/loans/
/api/v1/reservations/
/api/v1/notifications/
/api/v1/fines/
/api/v1/reviews/
/api/v1/dashboard/
```

Consult Swagger or ReDoc for current request fields and endpoint details.

---

## Current limitations

- Each book has one author, one genre, and one publisher in the current schema.
- Payment processing is mocked.
- SMS is represented in the notification model but requires an external SMS provider for real delivery.
- Local media files are not automatically restored after cloning the repository.
- The frontend depends on CDN-hosted Vue, Vue Router, Bootstrap, fonts, and icons.

---

## License

No license for the application source code is currently declared. Add a `LICENSE` file before distributing or publishing the project under a specific license.

Imported third-party datasets and cover images remain subject to their own licenses and usage terms.
