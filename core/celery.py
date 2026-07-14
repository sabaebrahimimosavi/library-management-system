"""
Celery application for the library management project.

Two periodic jobs replace the manual management commands that used to
be run by hand / via start.bat:
  - fines.tasks.calculate_fines_task      (was: manage.py calculate_fines)
  - notifications.tasks.send_due_date_reminders_task
        (was: manage.py send_due_date_reminders)

Both tasks call the same service-layer functions the old commands used,
so behavior is unchanged — only the trigger mechanism moves from
"run manually" to "run automatically on a schedule".
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Read CELERY_* settings from Django's settings.py (namespace="CELERY"
# means e.g. CELERY_BROKER_URL in settings.py maps to broker_url here).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app (fines/tasks.py,
# notifications/tasks.py, etc.).
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "calculate-fines-daily": {
        "task": "fines.tasks.calculate_fines_task",
        # Daily at 01:00 server time — same time the old crontab example used.
        "schedule": crontab(hour=1, minute=0),
    },
    "send-due-date-reminders-daily": {
        "task": "notifications.tasks.send_due_date_reminders_task",
        # Daily at 08:00 server time — same time the old crontab example used.
        "schedule": crontab(hour=8, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
