from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """
        Dev convenience: run the two daily management commands once when
        `runserver` starts, so fines/notifications are up to date without
        needing a cron/Celery-beat schedule set up locally.

        Guards:
        - only for `runserver`, never for migrate/shell/tests/etc, since
          those shouldn't have side effects on unrelated data
        - only in the actual reloaded child process (RUN_MAIN), so the
          autoreloader's parent process doesn't run it twice
        - each command is wrapped individually so a failure in one (e.g.
          DB not migrated yet on a first-ever run) doesn't block the other
          or crash server startup
        """
        import os
        import sys

        if "runserver" not in sys.argv:
            return
        if os.environ.get("RUN_MAIN") != "true":
            return

        from django.core.management import call_command

        for command in ("calculate_fines", "send_due_date_reminders"):
            try:
                call_command(command)
            except Exception as exc:  # pragma: no cover - startup convenience only
                print(f"[startup] '{command}' did not complete: {exc}")
