from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from mailing.models import Attempt


def send_mailing(mailing):
    """Отправляет письма всем получателям рассылки. Возвращает (bool, str)."""
    now = timezone.now()

    if not (mailing.start_time <= now <= mailing.end_time):
        return False, "Вне временного окна рассылки. Отправка запрещена."

    if not mailing.is_active:
        return False, "Рассылка отключена менеджером."

    recipients = mailing.recipients.all()
    if not recipients:
        return False, "Нет получателей для отправки."

    message = mailing.message
    attempts_to_create = []

    for recipient in recipients:
        try:
            send_mail(
                subject=message.subject,
                message=message.body,
                from_email=settings.EMAIL_FROM,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts_to_create.append(
                Attempt(
                    status=Attempt.STATUS_SUCCESS,
                    server_response="Письмо отправлено успешно.",
                    mailing=mailing,
                )
            )
        except Exception as exc:
            attempts_to_create.append(
                Attempt(
                    status=Attempt.STATUS_FAILED,
                    server_response=str(exc),
                    mailing=mailing,
                )
            )

    Attempt.objects.bulk_create(attempts_to_create)

    success_count = sum(
        1 for a in attempts_to_create if a.status == Attempt.STATUS_SUCCESS
    )
    fail_count = len(attempts_to_create) - success_count
    return True, f"Отправлено: {success_count} успешно, {fail_count} с ошибками."
