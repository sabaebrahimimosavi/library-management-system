import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationChannelService:
    """
    Thin adapter over actual delivery mechanisms. Email is fully implemented
    (via Django's email backend). SMS is a pluggable stub — wire in a real
    provider (Twilio, SNS, etc.) inside `send_sms` when ready.
    """

    @staticmethod
    def send_email(to_email: str, subject: str, message: str) -> None:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )

    @staticmethod
    def send_sms(to_phone: str, message: str) -> None:
        """
        Placeholder SMS delivery. Replace the body of this method with a
        real provider call (e.g. Twilio's `client.messages.create(...)`)
        when an SMS provider and a `phone_number` field on User are added.
        Raising NotImplementedError keeps failures visible instead of
        silently pretending to send.
        """
        raise NotImplementedError(
            "SMS delivery is not yet wired to a provider. "
            "Configure one in NotificationChannelService.send_sms()."
        )


class NotificationService:
    """
    Creates Notification records and dispatches them, with idempotency
    checks so re-running the daily reminder command never double-sends.
    """

    # ------------------------------------------------------------------
    # Core dispatch
    # ------------------------------------------------------------------
    @classmethod
    def _create_and_send(
        cls,
        *,
        user,
        notification_type: str,
        subject: str,
        message: str,
        loan=None,
        reservation=None,
    ) -> Notification:
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            subject=subject,
            message=message,
            loan=loan,
            reservation=reservation,
        )

        phone_number = getattr(user, "phone_number", None)
        channel = Notification.Channel.SMS if phone_number else Notification.Channel.EMAIL
        notification.channel = channel

        try:
            if channel == Notification.Channel.SMS:
                NotificationChannelService.send_sms(phone_number, message)
            else:
                NotificationChannelService.send_email(user.email, subject, message)
        except Exception as exc:  # noqa: BLE001 — log and record, don't crash callers
            logger.exception("Failed to deliver notification %s", notification.pk)
            notification.status = Notification.Status.FAILED
            notification.failure_reason = str(exc)
        else:
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()

        notification.save(
            update_fields=["channel", "status", "sent_at", "failure_reason"]
        )
        return notification

    # ------------------------------------------------------------------
    # Due-date reminders
    # ------------------------------------------------------------------
    @classmethod
    def notify_due_soon(cls, loan) -> Optional[Notification]:
        """
        Sends a "due in 2 days" reminder for `loan`. Idempotent: does
        nothing if this loan already has a DUE_SOON_REMINDER notification.
        """
        already_sent = Notification.objects.filter(
            loan=loan, notification_type=Notification.NotificationType.DUE_SOON_REMINDER
        ).exists()
        if already_sent:
            return None

        subject = "Reminder: your library book is due in 2 days"
        message = (
            f"Hi {loan.user.username},\n\n"
            f'"{loan.book}" is due on {loan.due_date}. '
            "Please return or renew it to avoid a fine.\n\n"
            "— The Library"
        )
        return cls._create_and_send(
            user=loan.user,
            notification_type=Notification.NotificationType.DUE_SOON_REMINDER,
            subject=subject,
            message=message,
            loan=loan,
        )

    @classmethod
    def notify_due_today(cls, loan) -> Optional[Notification]:
        """
        Sends a "due today" reminder for `loan`. Idempotent per loan.
        """
        already_sent = Notification.objects.filter(
            loan=loan, notification_type=Notification.NotificationType.DUE_TODAY_REMINDER
        ).exists()
        if already_sent:
            return None

        subject = "Reminder: your library book is due today"
        message = (
            f"Hi {loan.user.username},\n\n"
            f'"{loan.book}" is due today ({loan.due_date}). '
            "Please return it today to avoid a fine.\n\n"
            "— The Library"
        )
        return cls._create_and_send(
            user=loan.user,
            notification_type=Notification.NotificationType.DUE_TODAY_REMINDER,
            subject=subject,
            message=message,
            loan=loan,
        )

    # ------------------------------------------------------------------
    # Reservation availability
    # ------------------------------------------------------------------
    @classmethod
    def notify_reservation_available(cls, reservation) -> Optional[Notification]:
        """
        Notifies the reserving member that a copy of their reserved book
        is now available. Does NOT change reservation state — fulfillment
        only happens when the member actually borrows the book (see
        ReservationService.mark_fulfilled, called from LoanService).

        Idempotent: only one RESERVATION_AVAILABLE notification is ever
        sent per reservation, even if this is called again before the
        member acts on it.
        """
        already_sent = Notification.objects.filter(
            reservation=reservation,
            notification_type=Notification.NotificationType.RESERVATION_AVAILABLE,
        ).exists()
        if already_sent:
            return None

        subject = "Your reserved library book is available"
        message = (
            f"Hi {reservation.user.username},\n\n"
            f'A copy of "{reservation.book}" is now available. '
            "Please visit the library or borrow it through the app soon — "
            "reservations may expire if not acted on in time.\n\n"
            "— The Library"
        )
        return cls._create_and_send(
            user=reservation.user,
            notification_type=Notification.NotificationType.RESERVATION_AVAILABLE,
            subject=subject,
            message=message,
            reservation=reservation,
        )

# ------------------------------------------------------------------
    # Fines
    # ------------------------------------------------------------------
    @classmethod
    def notify_fine_issued(cls, fine) -> Optional[Notification]:
        """
        Notifies a member the first time a fine is issued on one of their
        loans. Idempotent per loan: only ever sends once, even if the
        fine amount is later recalculated upward while the loan remains
        overdue (FineService only calls this at creation time, but the
        idempotency check here is a second line of defense).
        """
        already_sent = Notification.objects.filter(
            loan=fine.loan,
            notification_type=Notification.NotificationType.FINE_ISSUED,
        ).exists()
        if already_sent:
            return None
 
        subject = "You have a library fine"
        message = (
            f"Hi {fine.user.username},\n\n"
            f'A fine of {fine.amount} has been applied for "{fine.loan.book}", '
            f"which is {fine.overdue_days} day(s) overdue. "
            "Please return the book if you haven't already, and settle the "
            "fine at your earliest convenience.\n\n"
            "— The Library"
        )
        return cls._create_and_send(
            user=fine.user,
            notification_type=Notification.NotificationType.FINE_ISSUED,
            subject=subject,
            message=message,
            loan=fine.loan,
        )
